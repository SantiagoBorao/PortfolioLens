import pandas as pd
import os

PORTFOLIOS = {
    "conservative": {
        "name": "Conservative Portfolio",
        "risk_profile": "Conservative",
        "benchmark_ticker": "AGG",
        "inception_date": "2023-01-02",
        "initial_value": 100_000,
        "allocations": {
            "AGG": 0.50, "JNJ": 0.15, "JPM": 0.15, "SPY": 0.20,
        },
    },
    "moderate": {
        "name": "Moderate Portfolio",
        "risk_profile": "Moderate",
        "benchmark_ticker": "SPY",
        "inception_date": "2023-01-02",
        "initial_value": 100_000,
        "allocations": {
            "SPY": 0.30, "MSFT": 0.15, "AAPL": 0.15,
            "AGG": 0.20, "QQQ": 0.10, "VWO": 0.10,
        },
    },
    "aggressive": {
        "name": "Aggressive Portfolio",
        "risk_profile": "Aggressive",
        "benchmark_ticker": "QQQ",
        "inception_date": "2023-01-02",
        "initial_value": 100_000,
        "allocations": {
            "AAPL": 0.15, "MSFT": 0.15, "GOOGL": 0.10,
            "ASML": 0.10, "QQQ": 0.15, "VWO": 0.10,
            "BTC-USD": 0.15, "ETH-USD": 0.10,
        },
    },
}


def generate_positions(prices_df):
    prices_df = prices_df.copy()
    prices_df["price_date"] = pd.to_datetime(prices_df["price_date"]).dt.date
    all_rows = []

    for pid, cfg in PORTFOLIOS.items():
        print(f"  {cfg['name']}...")
        inception  = pd.to_datetime(cfg["inception_date"]).date()
        init_value = cfg["initial_value"]
        allocs     = cfg["allocations"]

        pf = prices_df[
            prices_df["ticker"].isin(allocs) &
            (prices_df["price_date"] >= inception)
        ].copy()

        # calculate quantity to buy at inception (fixed, buy-and-hold)
        first_day_per_ticker = pf.groupby("ticker")["price_date"].min()
        first_prices = {}
        for ticker, fday in first_day_per_ticker.items():
            row = pf[(pf["ticker"] == ticker) & (pf["price_date"] == fday)]
            if not row.empty:
                first_prices[ticker] = float(row.iloc[0]["adj_close"])

        quantities = {
            t: (init_value * w) / first_prices[t]
            for t, w in allocs.items()
            if t in first_prices and first_prices[t] > 0
        }

        for day in sorted(pf["price_date"].unique()):
            day_px = pf[pf["price_date"] == day].set_index("ticker")["adj_close"].to_dict()
            total_val = sum(quantities.get(t, 0) * float(day_px.get(t, 0)) for t in allocs)

            for ticker, weight in allocs.items():
                if ticker not in quantities or ticker not in day_px:
                    continue
                qty   = quantities[ticker]
                price = float(day_px[ticker])
                mval  = qty * price
                wt    = mval / total_val if total_val > 0 else 0

                all_rows.append({
                    "price_date":            day,
                    "portfolio_id":          pid,
                    "portfolio_name":        cfg["name"],
                    "risk_profile":          cfg["risk_profile"],
                    "benchmark_ticker":      cfg["benchmark_ticker"],
                    "ticker":                ticker,
                    "quantity":              round(qty,      6),
                    "price":                 round(price,    4),
                    "market_value":          round(mval,     2),
                    "total_portfolio_value": round(total_val, 2),
                    "weight_pct":            round(wt * 100,  4),
                })

    df = pd.DataFrame(all_rows)

    # daily return and cumulative return per portfolio
    daily = (
        df.groupby(["portfolio_id", "price_date"])["market_value"]
        .sum().reset_index()
        .sort_values(["portfolio_id", "price_date"])
    )
    daily["daily_return"] = daily.groupby("portfolio_id")["market_value"].pct_change()
    daily["cumulative_return"] = daily.groupby("portfolio_id")["market_value"].transform(
        lambda x: x / x.iloc[0] - 1
    )

    df = df.merge(
        daily[["portfolio_id", "price_date", "daily_return", "cumulative_return"]],
        on=["portfolio_id", "price_date"],
        how="left",
    )
    return df.sort_values(["portfolio_id", "price_date", "ticker"]).reset_index(drop=True)


def generate_dim_portfolio():
    return pd.DataFrame([
        {
            "portfolio_id":     pid,
            "name":             cfg["name"],
            "risk_profile":     cfg["risk_profile"],
            "benchmark_ticker": cfg["benchmark_ticker"],
            "inception_date":   cfg["inception_date"],
            "initial_value":    cfg["initial_value"],
        }
        for pid, cfg in PORTFOLIOS.items()
    ])


if __name__ == "__main__":
    if not os.path.exists("data/raw_prices.csv"):
        raise FileNotFoundError("Run ingestion/fetch_prices.py first.")

    print("Loading prices...")
    prices_df = pd.read_csv("data/raw_prices.csv")

    print("Generating positions...")
    pos_df = generate_positions(prices_df)
    pos_df.to_csv("data/raw_positions.csv", index=False)

    pf_df = generate_dim_portfolio()
    pf_df.to_csv("data/dim_portfolios.csv", index=False)

    print(f"Saved {len(pos_df)} position rows to data/raw_positions.csv")
