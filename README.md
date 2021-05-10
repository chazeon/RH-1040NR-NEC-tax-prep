# RH 1040NR Schedule NEC Table

## Usage

1. Install Python 3 and script dependencies

    ```bash
    python3 -m pip install -r requirements.txt
    ```

1. Change `config.toml`

    1. Get your token from Robinhood and change "authorization" under
        `[requests.headers]` section.

1. Get orders / splits

    ```bash
    python3 scripts/fetch_orders.py
    python3 scripts/fetch_splits.py
    ```

1. Generate table in form 1040NR Schedule NEC format

    ```bash
    python3 scripts/make_nec.py
    ```

## Licence

Needs double check, use at your own descrete.  Licenced under WTFPL.