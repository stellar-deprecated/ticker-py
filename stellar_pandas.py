#!/usr/bin/python
import json, requests, sqlite3, sys
from datetime import date, timedelta
import pandas as pd

# TODO validate basevolume
# TODO fix get_cursor
# TODO loop through resolults and ensure that we have all the tx for the day

# UPDATE
FILENAME = '/var/www/tempo/public/fx/exchange.json'

def get_cursor(asset, asset_issuer):
    " get the cursor you want to start with"
    #c.execute('SELECT * FROM txs;')
    #print(c.fetchone())
    #conn = sqlite3.connect('trades.sqlite3')
    #c = conn.cursor()
    #conn.close()
    # bad hack fix
    cursor ='44327219295686657-1'
    return cursor


def get_book(cursor, asset, asset_issuer):
    q = "https://horizon.stellar.org/order_book/trades?selling_asset_type=credit_alphanum4&selling_asset_code=%s&selling_asset_issuer=%s&buying_asset_type=native&limit=100&order=desc" % (asset.upper(),asset_issuer) #, cursor)
    print q
    data = requests.get(q)
    sub_data = data.json()['_embedded']['records']
    # TODO fix this as it may not be all records
    return sub_data


def get_volume(cursor, asset, asset_issuer):
    q = "https://horizon.stellar.org/order_book?selling_asset_type=credit_alphanum4&selling_asset_code=%s&selling_asset_issuer=%s&buying_asset_type=native" % (asset.upper(),asset_issuer)
    data = requests.get(q)
    # TODO fix this as it may not be all records
    return data.json()


def get_last(df):
    last = df.ix[0]['sold_amount']/df.ix[0]['bought_amount']
    return round(last, 8)


def get_quoteVolume(dfbids, dfasks):

    bidvol = dfbids['amount'].sum()
    dfasks['lum'] = dfasks['amount'] * dfasks['price']
    askvol = dfasks['lum'].sum()
    return bidvol + askvol


def get_bids_asks(dfbook, asset):
    vol_label = asset.lower() + '_vol'
    price_label = 'xlm_price'
    asks = dfbook['asks']
    dfasks = pd.read_json(json.dumps(asks))
    dfasks[vol_label] = dfasks['amount'] * dfasks['price']
    dfasks[price_label] = 1/dfasks['price']
    bids = dfbook['bids']
    dfbids = pd.read_json(json.dumps(bids))
    dfbids[vol_label] = dfbids['amount'] * dfbids['price']
    dfbids[price_label] = 1/dfbids['price']
    return dfbids, dfasks


def get_dftrades(subdata, asset):
    asset_price_label = asset.lower() + '_price'
    xlm_price_label = 'xlm_price'
    pd.set_option('float_format', '{:20,.8f}'.format)
    dftrades = pd.read_json(json.dumps(subdata))
    dftrades['date'] = pd.DatetimeIndex(dftrades['created_at']).date
    dftrades['created_at'] = pd.to_datetime(dftrades['created_at'])
    dftrades[asset_price_label] = dftrades['bought_amount']/dftrades['sold_amount']
    dftrades['xlm_price'] = dftrades['sold_amount']/dftrades['bought_amount']
    dftrades.index = dftrades['created_at']
    today = str(date.today())
    yesterday = str(date.today() - timedelta(1))
    print ' ------------------ today -------------'
    dftr_today = dftrades.ix[today]
    print dftr_today
    print ' ------------------ yd -------------'
    dftr_yd = dftrades.ix[yesterday]
    print dftr_yd
    if dftr_today.empty is True: dftr_today = dftrades
    if dftr_yd.empty is True: dftr_yd = dftrades
    return dftrades, dftr_today, dftr_yd


def get_percentChange(dftr_today, dftr_yd):
    #get yesterday
    #"lowestAsk": round((1/dfbids.ix[0]['price']), 8),
    today = dftr_today.ix[0]['xlm_price']
    print today
    yd = dftr_yd.ix[0]['xlm_price']
    print yd
    change = (today - yd) / (yd)
    print change
    return '{:.2%}'.format(change)


def write_asset(f, asset, asset_issuer):
    pd.options.display.float_format = '{:20,.8f}'.format
    cursor = get_cursor(asset, asset_issuer)
    subdata = get_book(cursor, asset, asset_issuer)
    dftrades, dftr_today, dftr_yd = get_dftrades(subdata, asset)
    dfbook = get_volume(cursor, asset, asset_issuer)
    dfbids, dfasks = get_bids_asks(dfbook, asset)
    file_json = {}
    file_json[asset +'_XLM'] = {
    "last": format(get_last(dftr_today), '.8f'),
    "lowestAsk": str('%.8f' % (1/dfbids.ix[0]['price'])),
    "highestBid": str("%.8f" %(1/dfasks.ix[0]['price'])),
    "percentChange":   str(get_percentChange(dftr_today, dftr_yd)),
     # this is apparently wrong
    "baseVolume": dftr_today['bought_amount'].sum(),
    "quoteVolume": get_quoteVolume(dfbids, dfasks),
    "isFrozen":    "0",
    "high24hr":    str('%.8f' % (dftr_today['xlm_price'].max())),
    "low24hr": str('%.8f' % (dftr_today['xlm_price'].min()))}
    return file_json
 

if __name__ == "__main__":

    assets = [('EURT','GAP5LETOV6YIE62YAM56STDANPRDO7ZFDBGSNHJQIYGGKSMOZAHOOS2S'), \
            ('BTC','GATEMHCCKCY67ZUCKTROYN24ZYT5GK4EQZ65JJLDHKHRUZI3EUEKMTCH'), \
             ('CNY','GAREELUB43IRHWEASCFBLKHURCGMHE5IF6XSE7EXDLACYHGRHM43RFOX')]
    
    assets_json = []
    f = open(FILENAME,'w')
    for asset in assets:
        asset_json = write_asset(f, asset[0], asset[1])
        assets_json.append(asset_json)
    print json.dumps(assets_json)
    f.write(json.dumps(assets_json))
    f.close()
