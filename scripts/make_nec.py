import json
import toml
import arrow
from pprint import pprint
import pandas
from typing import NamedTuple, List
import math

config = toml.load("config.toml")

START_DATE = arrow.get(config["period"]["start_date"])
END_DATE = arrow.get(config["period"]["end_date"])

class TickerEvent(NamedTuple):
    etime: arrow.Arrow
    etype: str
    emeta: any

def process_ticker(ticker, orders, splits, merge = True):

    events: List[TickerEvent] = []
    for _, o in orders.iterrows():
        events.append(TickerEvent(
            arrow.get(o["last_transaction_at"]),
            "order",
            o,
        ))
    for _, s in splits.iterrows():
        events.append(TickerEvent(
            arrow.get(s["paid_at"]),
            "split",
            s,
        ))
    
    events = sorted(events, key=lambda e: e.etime)

    memory = []
    positions = []

    for e in events:
        if e.etype == "order":
            order = e.emeta
            curr_side = order["side"]
            other_side = "buy" if curr_side == "sell" else "sell"

            try: 
                outstand = {
                    curr_side: {
                        "price": float(order["average_price"]),
                        "quantity": float(order["quantity"]),
                        "at": e.etime
                    }
                }
            except Exception:
                continue

            for position in positions:

                if other_side in position.keys():

                    memory.append({
                        curr_side: outstand[curr_side].copy(),
                        other_side: position[other_side].copy()
                    })

                    qty = min(position[other_side]["quantity"], outstand[curr_side]["quantity"])

                    memory[-1][curr_side ]["quantity"] = qty
                    memory[-1][other_side]["quantity"] = qty

                    outstand[curr_side ]["quantity"] -= qty
                    position[other_side]["quantity"] -= qty


                    if e.etime < START_DATE or e.etime >= END_DATE:
                        memory.pop()

                if outstand[curr_side]["quantity"] == 0:
                    break

            if outstand[curr_side]["quantity"] != 0:
                positions.append(outstand)

            positions = [p for p in positions if list(p.values())[0]["quantity"] != 0]

        if e.etype == "split":

            split = e.emeta
            for position in positions:
                side = list(position.keys())[0]
                position[side]["price"   ] /= (float(split["split.multiplier"]) / float(split["split.divisor"]))
                position[side]["quantity"] *= (float(split["split.multiplier"]) / float(split["split.divisor"]))

        
    df = [] 
    for m in memory:
        df.append({
            "ticker": ticker,
            "acquired": m["buy"]["at"],
            "sold": m["sell"]["at"],
            "cost": m["buy"]["price"] * m["buy"]["quantity"],
            "sales": m["sell"]["price"] * m["sell"]["quantity"]
        })
        if df[-1]["cost"] <= df[-1]["sales"]:
            df[-1]["gain"] = - df[-1]["cost"] + df[-1]["sales"]
        if df[-1]["cost"] > df[-1]["sales"]:
            df[-1]["loss"] = + df[-1]["cost"] - df[-1]["sales"]

    df = pandas.DataFrame(df)

    residue = sum([
        list(p.values())[0]["quantity"] for p in positions
    ])
    if abs(residue) > .001:
        rside = list(positions[0].keys())[0]
        print(f"{ticker:>5} {residue:.04f} [{rside}-side]")

    if merge and len(df.index):

        df = [{
            "ticker": ticker,
            "acquired": df["acquired"].min(),
            "sold": df["sold"].max(),
            "cost": df["cost"].sum(),
            "sales": df["sales"].sum(),
        }]
        if df[-1]["cost"] <= df[-1]["sales"]:
            df[-1]["gain"] = - df[-1]["cost"] + df[-1]["sales"]
        if df[-1]["cost"] > df[-1]["sales"]:
            df[-1]["loss"] = + df[-1]["cost"] - df[-1]["sales"]
        
        df = pandas.DataFrame(df)

    return df


if __name__ == "__main__":

    with open("summary.json") as fp:
        orders = json.load(fp)
        orders = pandas.io.json.json_normalize(orders)

    with open("splits.json") as fp:
        splits = json.load(fp)
        splits = pandas.io.json.json_normalize(splits)

    nec = pandas.DataFrame()

    for ticker in orders["instrument.symbol"].unique():
        _orders = orders[orders["instrument.symbol"] == ticker]
        _instrument_ids = _orders["instrument.id"].unique().tolist()
        _splits = splits[
            (splits["split.old_instrument_id"].isin(_instrument_ids)) | \
            (splits["split.new_instrument_id"].isin(_instrument_ids))
        ]
        mem = process_ticker(ticker, _orders, _splits, True)
        mem["name"] = _orders.iloc[0]["instrument.name"]
        nec = nec.append(mem, ignore_index=True, sort=False)
    
nec["acquired"] = nec["acquired"].apply(lambda x: x.format("MM/DD/YYYY"))
nec["sold"] = nec["sold"].apply(lambda x: x.format("MM/DD/YYYY"))

nec = nec.sort_values("sold")
print(nec.to_string())

with open("nec.csv", "w") as fp:
    fp.write(nec.to_csv(index=None))

