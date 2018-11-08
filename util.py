import requests
from ratelimit import sleep_and_retry, limits

REQUEST_RATE_LIMIT = 50  # per sec


@sleep_and_retry
@limits(calls=REQUEST_RATE_LIMIT, period=1)
def get_json(*args):
    """proxy to requests.get with rate limiting and exception throwing for bad http status"""
    response = requests.get(*args)
    response.raise_for_status()
    return response.json()
