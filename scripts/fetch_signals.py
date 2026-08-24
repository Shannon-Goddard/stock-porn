import yfinance as yf
import csv
import json
import os
import math
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
OPTIONABLE_FILE = os.path.join(DATA_DIR, 'stocks_optionable.csv')
SIGNALS_FILE = os.path.join(DATA_DIR, 'signals.json')
METADATA_FILE = os.path.join(DATA_DIR, 'metadata.json')

TOP_PCT = 0.10   # top/bottom 10%
TOP_N = 5        # top 5 by dollar move

def load_optionable():
    stocks = {}
    with open(OPTIONABLE_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['options_available'] == 'TRUE':
                stocks[row['Symbol']] = {
                    'name': row['Name'],
                    'sector': row['Sector']
                }
    return stocks

def fetch_prices(tickers):
    print(f"Fetching prices for {len(tickers)} optionable stocks...")
    # Download all tickers in one batch request
    raw = yf.download(
        tickers=tickers,
        period='2d',        # need previous close to calc change
        interval='1d',
        group_by='ticker',
        auto_adjust=True,
        progress=False,
        threads=True
    )
    return raw

def parse_prices(raw, tickers, stock_info):
    results = []
    for ticker in tickers:
        try:
            if len(tickers) == 1:
                df = raw
            else:
                df = raw[ticker]

            if df is None or len(df) < 2:
                continue

            prev_close = float(df['Close'].iloc[-2])
            curr_close = float(df['Close'].iloc[-1])

            # Skip nan or zero values — rate limited or missing data
            if math.isnan(prev_close) or math.isnan(curr_close):
                continue
            if prev_close == 0 or curr_close == 0:
                continue

            change_dollar = round(curr_close - prev_close, 2)
            change_pct = round((change_dollar / prev_close) * 100, 2)

            # Skip if change is exactly zero — likely bad/missing data
            if change_dollar == 0.0:
                continue

            results.append({
                'ticker': ticker,
                'name': stock_info[ticker]['name'],
                'sector': stock_info[ticker]['sector'],
                'price': round(curr_close, 2),
                'changePct': change_pct,
                'changeDollar': change_dollar
            })
        except Exception:
            continue

    return results

def filter_top_pct(results, gainers=True):
    n = max(1, int(len(results) * TOP_PCT))
    if gainers:
        sorted_list = sorted(results, key=lambda x: x['changePct'], reverse=True)
    else:
        sorted_list = sorted(results, key=lambda x: x['changePct'])
    return sorted_list[:n]

def filter_top_dollar(results, gainers=True):
    if gainers:
        sorted_list = sorted(results, key=lambda x: x['changeDollar'], reverse=True)
    else:
        sorted_list = sorted(results, key=lambda x: x['changeDollar'])
    return sorted_list[:TOP_N]

def update_metadata(total_optionable, total_processed):
    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        metadata = {}

    metadata['signals'] = {
        'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        'optionable_stocks': total_optionable,
        'successfully_priced': total_processed
    }

    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

def main():
    # Load optionable stocks
    stock_info = load_optionable()
    tickers = list(stock_info.keys())
    print(f"Loaded {len(tickers)} optionable stocks")

    # Fetch all prices in one batch
    raw = fetch_prices(tickers)

    # Parse into usable list
    results = parse_prices(raw, tickers, stock_info)
    print(f"Successfully priced: {len(results)} stocks")

    if not results:
        print("No data returned — market may be closed or API issue")
        return

    # Calculate signals
    top_gainers = filter_top_pct(results, gainers=True)
    top_losers = filter_top_pct(results, gainers=False)
    dollar_gainers = filter_top_dollar(top_gainers, gainers=True)
    dollar_losers = filter_top_dollar(top_losers, gainers=False)

    print(f"Top 10% gainers:      {len(top_gainers)} stocks")
    print(f"Top 10% losers:       {len(top_losers)} stocks")
    print(f"Top {TOP_N} dollar gainers: {[s['ticker'] for s in dollar_gainers]}")
    print(f"Top {TOP_N} dollar losers:  {[s['ticker'] for s in dollar_losers]}")

    # Write signals.json
    signals = {
        'topGainers': top_gainers,
        'topLosers': top_losers,
        'dollarGainers': dollar_gainers,
        'dollarLosers': dollar_losers
    }

    with open(SIGNALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(signals, f, indent=2)

    print(f"Signals saved to data/signals.json")

    # Update metadata timestamp
    update_metadata(len(tickers), len(results))
    print(f"Metadata updated")

if __name__ == '__main__':
    main()
