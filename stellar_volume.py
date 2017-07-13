#!/usr/bin/env python3
import json, requests 
from datetime import datetime as dt 
from datetime import timedelta
import pandas as pd
import yaml

def this_page(yesterday, sub_data, up):
    lower = 0
    upper = int(up)
    if yesterday < pd.to_datetime(sub_data[upper]['created_at']): #go to next page
        return 0
    elif yesterday > pd.to_datetime(sub_data[lower]['created_at']): #none on this page
        return -1
    else: #returns number of relevant entries on this page
        while upper-lower > 0:
            index = (upper + lower + 1)//2
            if yesterday > pd.to_datetime(sub_data[upper]['created_at']):
                upper = index
            elif yesterday < pd.to_datetime(sub_data[lower]['created_at']):
                lower = index
            else:
                return 0
        return lower
            
def get_book(assets):
    print("-------------------------------------------------------------- {} / {} ---------------------------------------------------------------".format(assets['base'], assets['counter']))
    data = {}
    entries = 0
    link = get_link(assets)
    print(link)
    yesterday = dt.now() - timedelta(hours=17)
    while True:
        json = requests.get(link)
        sub_data = json.json()['_embedded']['records']
        upper = len(sub_data) - 1
        if upper < 0: #There are no transactions
            return data
        index = 0
        result = this_page(yesterday, sub_data, upper)
        if result == 0: #next page
            while index<upper+1: #load entire page as data
                data[entries] = sub_data[index]
                entries += 1
                index += 1
        elif result == -1: #done
            return data #return data
        else: #this page
            while index<result: #load relevant info from this page
                data[entries] = sub_data[index]
                entries += 1
                index += 1
            return data #return data
        link = json.json()['_links']['next']['href']
        link.replace("\u0026", "&")   #TODO Needs to be removed when horizon bug is fixed

def get_link(assets):
    if assets['counter'] == 'XLM':
        link = "https://horizon.stellar.org/order_book/trades?selling_asset_type=credit_alphanum4&selling_asset_code={}&selling_asset_issuer={}&buying_asset_type=native&limit=200&order=desc".format(assets['base'], assets['base_issuer'])
    elif assets['base'] == 'XLM':
        link = "https://horizon.stellar.org/order_book/trades?selling_asset_type=native&buying_asset_type=credit_alphanum4&buying_asset_code={}&buying_asset_issuer={}&limit=200&order=desc".format(assets['counter'], assets['counter_issuer'])
    else:
        link = "https://horizon.stellar.org/order_book/trades?selling_asset_type=credit_alphanum4&selling_asset_code={}&selling_asset_issuer={}&buying_asset_type=credit_alphanum4&buying_asset_code={}&buying_asset_issuer={}&limit=200&order=desc".format(assets['base'], assets['base_issuer'], assets['counter'], assets['counter_issuer'])
    return link

def get_volume(sub_data):
    seller_volume = 0.0
    buyer_volume = 0.0
    index = 0
    for index, item in enumerate(sub_data):
        buyer_volume += float(sub_data[index]['sold_amount'])
        seller_volume += float(sub_data[index]['bought_amount'])
    print("base_volume = {}        counter_volume= {}".format(buyer_volume, seller_volume))
    return buyer_volume, seller_volume

def get_price(assets):
    link = get_link(assets)
    json = requests.get(link)
    sub_data = json.json()['_embedded']['records']
    if sub_data:
        sold = float(sub_data[0]['sold_amount'])
        bought = float(sub_data[0]['bought_amount'])
        return bought/sold
    else:
        return 0.0
    
def write_asset(assets):
    pd.options.display.float_format = '{:20,.8f}'.format
    subdata = get_book(assets)
    buyer_volume, seller_volume = get_volume(subdata)
    price = get_price(assets)
    file_json = {}
    file_json[assets['base'] + '_' + assets['counter']] = {
        "base_volume": format(buyer_volume, '.8f'),
        "counter_volume": format(seller_volume, '.8f'),
        "price": format(price, '.8f')}
    return file_json

def get_assets():
    f = open('config.yml', 'r')
    assets = {}
    config = yaml.load(f)
    for item in config:
        assets[item] = config[item]
    f.close()
    return assets

if __name__ == "__main__":
    assets_json = []
    f = open('exchange.json', 'w')
    assets = get_assets()
    for asset in assets:
        asset_json = write_asset(assets[asset])
        assets_json.append(asset_json)
    f.write(json.dumps(assets_json))
    f.close()
