#!/usr/bin/env python

# script to generate pairs.toml file for the ticker.json using the all assets endpoint

import requests

# minimum number of account holders to be added to the list if auth_required is true
min_account_holders_auth_required = 1
# minimum number of account holders to be added to the list if auth_required is false
min_account_holders = 50
# minimum number of issued assets to be added to the list
min_issued_assets = 10

blacklist_code = ['REMOVE', 'XLM']
# transform name for asset based on code:issuer whitelist
name_transforms = {
    'XCN:GCNY5OXYSY4FKHOPT2SPOQZAOEIGXB5LBYW3HVU3OWSTQITS65M5RCNY': 'CNY',
    'EURT:GAP5LETOV6YIE62YAM56STDANPRDO7ZFDBGSNHJQIYGGKSMOZAHOOS2S': 'EUR',
    'HKDT:GABSZVZBYEO5F4V5LZKV7GR4SAJ5IKJGGOF43BIN42FNDUG7QPH6IMRQ': 'HKD',
    'WSD:GDSVWEA7XV6M5XNLODVTPCGMAJTNBLZBXOFNQD3BNPNYALEYBNT6CE2V' : 'USD',
    'USDT:GBOXNWGBB7SG3NVIA7O25M7JIRSXQ4KKU3GYARJEFMQXSR3APF3KRI6S' : 'USD',
    'NGNT:GAWODAROMJ33V5YDFY3NPYTHVYQG7MJXVJ2ND3AOGIHYRWINES6ACCPD' : 'NGN'
}
# always include these token pairs
whitelist = {
    'BTC:GDXTJEK4JZNSTNQAWA53RZNS2GIKTDRPEUWDXELFMKU52XNECNVDVXDI': 1,
    'BTC:GBSTRH4QOTWNSVA6E4HFERETX4ZLSR3CIUBLK7AXYII277PFJC4BBYOG': 1
}

print('''[[pair]]
name = "EUR_PHP"
base_asset_code = "EURT"
base_asset_issuer = "GAP5LETOV6YIE62YAM56STDANPRDO7ZFDBGSNHJQIYGGKSMOZAHOOS2S"
counter_asset_code = "PHP"
counter_asset_issuer = "GBUQWP3BOUZX34TOND2QV7QQ7K7VJTG6VSE7WMLBTMDJLLAW7YKGU6EP"

[[pair]]
name = "BTC_XEL"
base_asset_code = "BTC"
base_asset_issuer = "GATEMHCCKCY67ZUCKTROYN24ZYT5GK4EQZ65JJLDHKHRUZI3EUEKMTCH"
counter_asset_code = "XEL"
counter_asset_issuer = "GAXELY4AOIRVONF7V25BUPDNKZYIVT6CWURG7R2I6NQU26IQSQODBVCS"
''')

next_url = "https://horizon.stellar.org/assets?limit=200"
while True:
    req = requests.get(next_url)
    o = req.json()
    next_url = o['_links']['next']['href']
    records = o['_embedded']['records']

    for r in records:
        key = r['asset_code'] + ':' + r['asset_issuer']
        if key not in whitelist:
            if r['asset_code'] in blacklist_code:
                continue

            if r['flags']['auth_required']:
                account_limit = min_account_holders_auth_required
            else:
                account_limit = min_account_holders
            if r['num_accounts'] < account_limit:
                continue

            if float(r['amount']) < min_issued_assets:
                continue

        # display
        print('[[pair]]')
        # check transform map before printing out name field
        name_code = r['asset_code']
        if key in name_transforms:
            name_code = name_transforms[key]
        print('name = "XLM_' + name_code + '"')
        print('base_asset_code = "XLM"')
        print('base_asset_issuer = "native"')
        print('counter_asset_code = "' + r['asset_code'] + '"')
        toml_link = r['_links']['toml']['href']
        if len(toml_link) > 0:
            print('# toml = ' + toml_link)
        print('counter_asset_issuer = "' + r['asset_issuer'] + '"')
        print('')

    # stopping case
    if len(records) == 0:
        break
