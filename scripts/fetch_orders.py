import json
import requests
from io import BytesIO
from rh import _get_info, _rgetv
from tqdm.cli import tqdm
from copy import copy

if __name__ == "__main__":

    i = 0
    next_url = "https://api.robinhood.com/orders/"
    orders = []

    while next_url != None:
        resp = _get_info(next_url)
        next_url = resp["next"]
        orders.extend(resp["results"])
        i += 1
    
    with tqdm(total=len(orders)) as pbar:
        for order in orders:
            for key in ["instrument", "position", "instrument.splits"]:
                try:
                    _keys = key.split(".")
                    _url = _rgetv(order, _keys)
                    _rgetv(order, _keys[:-1])[_keys[-1]] = copy(_get_info(_url))
                except KeyError as e:
                    continue
            pbar.update(1)

with open("summary.json", "w") as fp:
    json.dump(orders, fp)