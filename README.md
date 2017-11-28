# Stellar Ticker #

A script to aggregate curated trade data from Stellar and dump it to a JSON file. 

## Input ##

A TOML file containing a list of asset pairs formatted as following: 

```toml
[[pair]]
name = "XLM_BTC"
base_asset_code = "XLM"
base_asset_issuer = "native"
counter_asset_code = "BTC"
counter_asset_issuer = "GDXTJEK4JZNSTNQAWA53RZNS2GIKTDRPEUWDXELFMKU52XNECNVDVXDI"
```

Note: 
- The `name` field can contain any arbitrary string but should be a meaningful description of the pair. 
- Pairs that share the same `name` will be aggregated together. This allows for multiple anchors of, for example, 
`BTC` to share a ticker entry.

## Output ##
```json
{
    "generated_at": 1511810991594, 
    "pairs": [
        {
            "base_volume": "9025.0000000", 
            "counter_volume": "0.0505390", 
            "name": "XLM_BTC", 
            "price": "0.0000056", 
            "trade_count": 3
        }
    ]
}
```

Note: 
- `generated_at` is timestamp of generation, represented as millis since epoch.
- `base_volume` is total aggregated base asset volume traded. String representation of a float with 7 digits after the decimal point.
- `counter_volume` is a total aggregated counter asset volume traded. String representation of a float with 7 digits after the decimal point.
- `name` correlates to the input pair name.
- `trade_count` is a total count of aggregated trades.
- `price` is an average calculated as `counter_volume/base_volume`.
  
## Install ##
Assuming python 2 and pip are installed 

```bash
$ pip install -r requirements.txt
```
  
## Run ## 

To run with default settings: 
```bash
$ python ticker.py
```

### Configuration
```bash
$ python ticker.py -h
usage: ticker.py [-h] [-c PAIRS_TOML] [-u HORIZON_HOST] [-t TIME_DURATION]
                 [-bt BUCKET_RESOLUTION] [-o OUTPUT_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -c PAIRS_TOML, --pairs_toml PAIRS_TOML
                        path to toml file containing asset pairs (default:
                        pairs.toml)
  -u HORIZON_HOST, --horizon_host HORIZON_HOST
                        horizon host, including scheme (default:
                        https://horizon.stellar.org/)
  -t TIME_DURATION, --time_duration TIME_DURATION
                        time duration in millis, defaults to 24 hours
                        (default: 86400000)
  -b BUCKET_RESOLUTION, --bucket_resolution BUCKET_RESOLUTION
                        buc**ket resolution for aggregation in millis, default
                        to 5 minutes (default: 300000)
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        output file path (default: ticker.json)
```