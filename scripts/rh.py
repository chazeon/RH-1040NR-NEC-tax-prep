
import requests
from functools import lru_cache
import toml

config = toml.load("config.toml")

@lru_cache()
def _get_info(url: str):
    resp = requests.get(url, headers=config["requests"]["headers"])
    return resp.json()

def _rgetv(d, keys):
    return d if len(keys) == 0 else _rgetv(d[keys[0]], keys[1:])
