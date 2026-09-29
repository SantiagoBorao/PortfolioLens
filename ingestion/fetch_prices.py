import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

ASSETS = {
    "AAPL":    {"name": "Apple",                "type": "Stock",  "sector": "Technology",   "country": "USA"},
    "MSFT":    {"name": "Microsoft",            "type": "Stock",  "sector": "Technology",   "country": "USA"},
    "GOOGL":   {"name": "Alphabet",             "type": "Stock",  "sector": "Technology",   "country": "USA"},
    "JPM":     {"name": "JPMorgan Chase",       "type": "Stock",  "sector": "Finance",      "country": "USA"},
    "JNJ":     {"name": "Johnson & Johnson",    "type": "Stock",  "sector": "Healthcare",   "country": "USA"},
    "SAN.MC":  {"name": "Santander",            "type": "Stock",  "sector": "Finance",      "country": "ESP"},
    "ITX.MC":  {"name": "Inditex",              "type": "Stock",  "sector": "Consumer",     "country": "ESP"},
    "ASML":    {"name": "ASML",                 "type": "Stock",  "sector": "Technology",   "country": "NLD"},
    "SPY":     {"name": "S&P 500 ETF",          "type": "ETF",    "sector": "Broad Market", "country": "USA"},
    "QQQ":     {"name": "Nasdaq 100 ETF",       "type": "ETF",    "sector": "Technology",   "country": "USA"},
    "AGG":     {"name": "US Bond ETF",          "type": "ETF",    "sector": "Fixed Income", "country": "USA"},
    "VWO":     {"name": "Emerging Markets ETF", "type": "ETF",    "sector": "Broad Market", "country": "EMG"},
    "BTC-USD": {"name": "Bitcoin",              "type": "Crypto", "sector": "Crypto",       "country": "N/A"},
    "ETH-USD": {"name": "Ethereum",             "type": "Crypto", "sector": "Crypto",       "country": "N/A"},
}

BENCHMARKS = {
    "SPY": {"name": "S&P 500 ETF",    "type": "Benchmark", "sector": "Broad Market", "country": "USA"},
    "AGG": {"name": "US Bond ETF",    "type": "Benchmark", "sector": "Fixed Income", "country": "USA"},
    "QQQ": {"name": "Nasdaq 100 ETF", "type": "Benchmark", "sector": "Technology",   "country": "USA"},
}


def fetch_prices(tickers, years=2):
    end   = datetime.today()
    start = end - timedelta(days=years * 365)
    rows  = []

    for ticker, meta in tickers.items():
        print(f"  {ticker}...")
        try:
            raw = yf.download(
                ticker,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True,
            )
            if raw.empty:
                print(f"  [skip] no data for {ticker}")
                continue

            # yfinance sometimes returns MultiIndex columns with auto_adjust=True
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)

            raw = raw.reset_index()
            raw.columns = [str(c).lower().replace(" ", "_") for c in raw.columns]

            for k, v in meta.items():
                raw[k] = v
            raw = raw.rename(columns={"name": "asset_name", "type": "asset_type"})
            rows.append(raw)

        except Exception as exc:
            print(f"  [error] {ticker}: {exc}")

    if not rows:
        raise ValueError("No assets downloaded.")

    df = pd.concat(rows, ignore_index=True)
    df = df.rename(columns={"date": "price_date"})

    if "adj_close" not in df.columns:
        df["adj_close"] = df["close"]

    keep = ["price_date", "ticker", "asset_name", "asset_type",
            "sector", "country", "open", "high", "low",
            "close", "adj_close", "volume"]
    df = df[[c for c in keep if c in df.columns]]
    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date
    df = df.sort_values(["ticker", "price_date"]).reset_index(drop=True)
    return df


if __name__ == "__main__":
    tickers = {**ASSETS, **{k: v for k, v in BENCHMARKS.items() if k not in ASSETS}}
    print("Fetching prices...")
    df = fetch_prices(tickers, years=2)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/raw_prices.csv", index=False)
    print(f"Saved {len(df)} rows to data/raw_prices.csv")
    print(df.head())
