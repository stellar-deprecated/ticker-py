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
- `trade_count` is a total count of trades for the given time period.
- `price` is an average calculated as `counter_volume/base_volume`
  
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
$ python ticker.py --help
usage: ticker.py [-h] [--pairs_toml PAIRS_TOML] [--horizon_host HORIZON_HOST]
                 [--time_duration TIME_DURATION]
                 [--bucket_resolution BUCKET_RESOLUTION]
                 [--output_file OUTPUT_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --pairs_toml PAIRS_TOML
                        path to toml file containing asset pairs (default:
                        pairs.toml)
  --horizon_host HORIZON_HOST
                        horizon host, including scheme (default:
                        https://horizon.stellar.org/)
  --time_duration TIME_DURATION
                        time duration in millis (default: 86400000)
  --bucket_resolution BUCKET_RESOLUTION
                        bucket resolution for aggregation in millis (default:
                        300000)
  --output_file OUTPUT_FILE
                        output file path (default: ticker.json)


```