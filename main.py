from datetime import datetime
from pathlib import Path
from typing import Union
from io import StringIO

import pandas as pd
import numpy as np
import requests


URL     = "https://dse.co.tz/"
FILE    = "ohlcv.csv"
COLUMNS = [
    "date", "ticker", "high", "low", "open",
    "prev close", "close", "change", "% change",
    "volume", "turnover", "deals", "bids",
    "offers", "mktcap"
]


def loader() -> pd.DataFrame:
    """Load existing OHLCV data."""
    
    if Path(FILE).exists():
        return pd.read_csv(FILE)
        
    df = df.drop_duplicates(subset=["date", "ticker"], keep="last")
    return pd.DataFrame(columns=COLUMNS)


def collection(url: str = URL) -> pd.DataFrame:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    tables     = pd.read_html(StringIO(response.text))
    df         = tables[3].copy()
    df["Date"] = datetime.today().date()
    return df


def cleaning(df: pd.DataFrame) -> pd.DataFrame:
    df            = df.copy()
    df["Symbol"]  = (df["Symbol"].astype(str).str.strip().str.upper())
    df["Date"]    = pd.to_datetime(df["Date"])
    df["Change"]  = (df["Change"]
                        .astype("string")
                        .str.extract(r"([-+]?\d+(?:\.\d+)?)", expand=False)
                        .astype(float)
                        )
    
    df = df.rename(columns={
            "Symbol"            : "Ticker",
            "Turn over"         : "Turnover",
            "MCAP (TZS 'B)"     : "mktcap",
            "Out Standing Bid"  : "Bids",
            "Out Standing Offer": "Offers"
        })

   
    df["% Change"] = (df["Change"])
    df["Change"] = ((df["Change"] / 100)* pd.to_numeric(df["Prev Close"])).round(0)
    
    df = df.rename(columns={col: col.lower() for col in df.columns})

    for col in df.columns.difference(["date", "ticker"]):
        df[col] = (df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("TZS", "", regex=False)
            .str.strip()
            .pipe(pd.to_numeric, errors="coerce")
            .replace(0, np.nan)
            )

    df = df.drop_duplicates(subset=["date", "ticker"], keep="last")
    return df[COLUMNS].copy()


def main():
    collected        = collection()                # 1. Collect
    new_cleaned      = cleaning(collected)         # 2. Clean new data
    existing         = loader()                    # 3. Load existing data
    
    combined         = pd.concat([existing, new_cleaned], ignore_index=True)
    combined["date"] = (pd.to_datetime(combined["date"], format="mixed").dt.strftime("%Y-%m-%d"))
    combined         = (combined.drop_duplicates(subset=["date", "ticker"], keep="last")
                        .sort_values(["date", "ticker"], ascending=False)
                        .reset_index(drop=True)
                        )

    COLUMNS = ["date", "ticker", "open", "high", "low", "close", "change", "% change", 
               "volume", "turnover", "deals", "bids",
                "offers", "mktcap"
                ]
    final = combined[COLUMNS].copy(

    final.to_csv(FILE, index=False)
    return None
    


if __name__ == "__main__":
    main()
