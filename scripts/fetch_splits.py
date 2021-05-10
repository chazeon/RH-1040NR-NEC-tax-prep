import json
from rh import _get_info, _rgetv

with open("summary.json") as fp:
    orders = json.load(fp)

splits=_get_info(
    "https://api.robinhood.com/corp_actions/v2/split_payments/?instrument_ids=" + ",".join(
        set([order["instrument"]["id"] for order in orders])
    )
)["results"]

with open("splits.json", "w") as fp:
    json.dump(splits, fp)