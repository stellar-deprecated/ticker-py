#!/usr/bin/env python

from time import time, sleep
import json
import toml
import argparse
from urllib import urlencode
from collections import namedtuple
from datetime import datetime
from dateutil import parser

from util import get_json

PAGE_LIMIT = 200  # for aggregation endpoint


def millis():
    """current time in millis since epoch"""
    return int(round(time() * 1000))


def make_asset_params(prefix, atype, code, issuer):
    """get aggregation request parameters for single asset"""
    return {
        prefix + "_asset_type": atype,
        prefix + "_asset_code": code,
        prefix + "_asset_issuer": issuer,
    }


def make_asset_param_from_pair(pair, prefix):
    """get aggregation parameters for asset pair"""
    if pair[prefix + "_asset_issuer"] == "native":
        return make_asset_params(prefix, "native", "", "")
    else:
        asset_code = pair[prefix + "_asset_code"]
        if len(asset_code) > 12:
            raise ValueError("asset code longer than 12 characters")
        asset_type = "credit_alphanum4" if len(asset_code) <= 4 else "credit_alphanum12"
        asset_issuer = pair[prefix + "_asset_issuer"]
        return make_asset_params(prefix, asset_type, asset_code, asset_issuer)


def make_aggregation_params(pair, start, end, resolution):
    """get aggregation request params"""
    params = {
        "order": "asc",
        "limit": PAGE_LIMIT,
        "start_time": start,
        "end_time": end,
        "resolution": resolution
    }
    params.update(make_asset_param_from_pair(pair, "base"))
    params.update(make_asset_param_from_pair(pair, "counter"))
    return params


def sum_tuples(t1, t2):
    """sum all items in two tuples to a third one. tuples must match in size"""
    return tuple(sum(t) for t in zip(t1, t2))


def record_to_tuple(record):
    """convert aggregation record to (base_volume, counter_volume, trade_count) tuple"""
    return float(record["base_volume"]), float(record["counter_volume"]), int(record["trade_count"])


def aggregate_pair(horizon_host, pair, start, end, resolution):
    """
    fetch all trades from given time period and aggregate
    :return a tuple of (base_volume, counter_volume, trade_count)
    """
    print "aggregating pair:", pair["name"]
    values = (0, 0, 0)
    params = make_aggregation_params(pair, start, end, resolution)
    url = horizon_host + "/trade_aggregations?" + urlencode(params)
    consumed = False
    sleep(1)
    while not consumed:
        print "fetching url:", url
        json_result = get_json(url)
        records = json_result['_embedded']['records']
        for record in records:
            values = sum_tuples(values, record_to_tuple(record))
        consumed = len(records) < PAGE_LIMIT
        url = json_result["_links"]["next"]["href"]
    return values


def aggregate_pairs(horizon_host, pairs, start, end, resolution):
    """
    perform aggregation on all given pairs and group by the pair name
    :return a dictionary where keys are a pair name and value is an
    aggregated tuple of (base_volume, counter_volume, trade_count)
    """
    retval = {}
    for pair in pairs:
        name = pair["name"]
        if name not in retval:
            retval[name] = (0, 0, 0)
        retval[name] = sum_tuples(retval[name], aggregate_pair(horizon_host, pair, start, end, resolution))
    return retval


def format_pair_result(pair_name, pair_tuple, price):
    """convert trade aggregation tuple to a readable dictionary"""
    return {
        "name": pair_name,
        "base_volume": "%.7f" % pair_tuple[0],
        "counter_volume": "%.7f" % pair_tuple[1],
        "trade_count": pair_tuple[2],
        "price": "%.7f" % price
    }


def dump_aggregated_pairs(aggregated_at, aggregated_pairs, prices_dict, output):
    """format aggregated pairs and dump as json to file"""
    formatted_pairs = [format_pair_result(pair_name, pair_tuple, prices_dict[pair_name].price)
                       for pair_name, pair_tuple in aggregated_pairs.iteritems()]
    with open(output, 'w') as outfile:
        json.dump({
            "pairs": formatted_pairs,
            "generated_at": aggregated_at
        }, outfile, indent=4, sort_keys=True)
    print "results written to", output


def make_trade_params(pair):
    """get aggregation request params"""
    params = {
        "order": "desc",
        "limit": 1,
    }
    params.update(make_asset_param_from_pair(pair, "base"))
    params.update(make_asset_param_from_pair(pair, "counter"))
    return params


DatedPrice = namedtuple('DatedPrice', ['date', 'price'])


def get_price(horizon_host, pair):
    """return last trade price as DatedPrice"""
    print "fetching latest price for:" + pair["name"]
    params = make_trade_params(pair)
    json_result = get_json(horizon_host + "/trades", params)
    try:
        trade_record = json_result["_embedded"]["records"][0]
    except IndexError:
        return DatedPrice(date=datetime.utcfromtimestamp(0), price=0)
    price = float(trade_record["price"]["n"]) / float(trade_record["price"]["d"])
    timestamp = parser.parse(trade_record["ledger_close_time"], ignoretz=True)
    return DatedPrice(date=timestamp, price=price)


def latest_date_price(dated_price_a, dated_price_b):
    """return latest of both DatedPrices"""
    return dated_price_a if dated_price_a.date > dated_price_b.date else dated_price_b


def get_prices(horizon_host, pairs):
    """return a dict of pair name to latest DatedPrice"""
    dated_prices = [(pair["name"], get_price(horizon_host, pair)) for pair in pairs]
    price_dict = {}
    for dated_price in dated_prices:
        if dated_price[0] not in price_dict:
            price_dict[dated_price[0]] = dated_price[1]
        else:
            price_dict[dated_price[0]] = latest_date_price(price_dict[dated_price[0]], dated_price[1])
    return price_dict


def main():
    """configure commandline arguments and initiate aggregation"""
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-c", "--pairs_toml", default="pairs.toml", help="path to toml file containing asset pairs")
    parser.add_argument("-u", "--horizon_host", default="https://horizon.stellar.org",
                        help="horizon host, including scheme")
    parser.add_argument("-t", "--time_duration", type=int, default=86400000,
                        help="time duration in millis, defaults to 24 hours")
    parser.add_argument("-b", "--bucket_resolution", type=int, default=60000,
                        help="bucket resolution for aggregation in millis, defaults to 5 minutes")
    parser.add_argument("-o", "--output_file", default="ticker.json", help="output file path")
    args = parser.parse_args()

    config = toml.load(args.pairs_toml)
    now = millis()
    end_time = now - (now % args.bucket_resolution)
    aggregated_pairs = aggregate_pairs(args.horizon_host, config["pair"], end_time - args.time_duration, end_time,
                                       args.bucket_resolution)
    pair_prices_dict = get_prices(args.horizon_host, config["pair"])
    dump_aggregated_pairs(now, aggregated_pairs, pair_prices_dict, args.output_file)


if __name__ == "__main__":
    main()
