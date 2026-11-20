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

TOP_N_PCT = 10   # top 10 by percent move
TOP_N = 5        # top 5 by dollar move
MIN_PRICE = 10.00       # options liquidity floor — sub-$10 spreads are untradeable
MIN_AVG_VOLUME = 500000 # daily volume floor — low volume = no options open interest

# Sector -> ETF mapping for sector_etf_change lookup at entry
SECTOR_ETF_MAP = {
    'Technology':             'XLK',
    'Tech':                   'XLK',
    'Communication Services': 'XLC',
    'Consumer Discretionary': 'XLY',
    'Consumer Staples':       'XLP',
    'Energy':                 'XLE',
    'Financials':             'XLF',
    'Health Care':            'XLV',
    'Healthcare':             'XLV',
    'Industrials':            'XLI',
    'Materials':              'XLB',
    'Real Estate':            'VNQ',
    'Utilities':              'XLU',
    'Biotechnology':          'XBI',
    'Biotech':                'XBI',
    'Defense':                'ITA',
    'Retail':                 'XRT',
    'Regional Banks':         'KRE',
    'Crypto':                 'BITO',
}

# NYSE early close days — market closes 1 PM EST (21:00 UTC)
# Signals runs every 30 min — block writes after close to prevent garbage data
EARLY_CLOSE_DATES = {
    '2025-11-28', '2025-12-24',
    '2026-11-27', '2026-12-24',
    '2027-11-26', '2027-12-24',
}
EARLY_CLOSE_UTC_HOUR = 21


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

def get_sector_fallback(ticker):
    """Fetch sector from yfinance info when CSV has blank sector."""
    try:
        info = yf.Ticker(ticker).info
        return info.get('sector') or info.get('industry') or 'Unknown'
    except Exception:
        return 'Unknown'

def parse_prices(raw, tickers, stock_info):
    results = []
    counts = {
        'total': len(tickers),
        'no_data': 0,
        'bad_values': 0,
        'zero_change': 0,
        'below_min_price': 0,
        'below_min_volume': 0,
        'passed': 0
    }
    for ticker in tickers:
        try:
            if len(tickers) == 1:
                df = raw
            else:
                df = raw[ticker]

            if df is None or len(df) < 2:
                counts['no_data'] += 1
                continue

            prev_close = float(df['Close'].iloc[-2])
            curr_close = float(df['Close'].iloc[-1])

            if math.isnan(prev_close) or math.isnan(curr_close) or prev_close == 0 or curr_close == 0:
                counts['bad_values'] += 1
                continue

            change_dollar = round(curr_close - prev_close, 2)
            change_pct = round((change_dollar / prev_close) * 100, 2)

            if change_dollar == 0.0:
                counts['zero_change'] += 1
                continue

            # Quality filters — see docs/methodology.md Signal Quality Filters section
            if curr_close < MIN_PRICE:
                counts['below_min_price'] += 1
                continue
            avg_vol = df['Volume'].mean()
            if math.isnan(avg_vol) or avg_vol < MIN_AVG_VOLUME:
                counts['below_min_volume'] += 1
                continue

            counts['passed'] += 1
            sector = stock_info[ticker]['sector'].strip() if stock_info[ticker]['sector'].strip() else get_sector_fallback(ticker)
            results.append({
                'ticker': ticker,
                'name': stock_info[ticker]['name'],
                'sector': sector,
                'sector_etf': SECTOR_ETF_MAP.get(sector),
                'price': round(curr_close, 2),
                'changePct': change_pct,
                'changeDollar': change_dollar,
                'signal_first_appeared': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            })
        except Exception:
            counts['no_data'] += 1
            continue

    return results, counts

def has_liquid_options(ticker, stock_price):
    """
    Quick check: does this ticker have at least one options expiry within 7 days
    with a contract near ATM under $1.00 ask?
    Rejects candidates like CGON that pass price/volume filters but have no tradeable contract.
    """
    try:
        t = yf.Ticker(ticker)
        exps = t.options
        if not exps:
            return False
        today = datetime.now(timezone.utc).date()
        for exp_str in exps:
            from datetime import date as date_
            exp_date = datetime.strptime(exp_str, '%Y-%m-%d').date()
            dte = (exp_date - today).days
            if 1 <= dte <= 7:
                chain = t.option_chain(exp_str)
                for df in [chain.calls, chain.puts]:
                    if df is None or df.empty:
                        continue
                    near = df[abs(df['strike'] - stock_price) < stock_price * 0.15]
                    if not near.empty:
                        asks = near['ask'].dropna()
                        if any((asks > 0) & (asks <= 1.00)):
                            return True
        return False
    except Exception:
        return False


def filter_top_pct(results, gainers=True):
    if gainers:
        sorted_list = sorted(results, key=lambda x: x['changePct'], reverse=True)
    else:
        sorted_list = sorted(results, key=lambda x: x['changePct'])
    return sorted_list[:TOP_N_PCT]

def filter_top_dollar(results, gainers=True):
    if gainers:
        sorted_list = sorted(results, key=lambda x: x['changeDollar'], reverse=True)
    else:
        sorted_list = sorted(results, key=lambda x: abs(x['changeDollar']), reverse=True)
    return sorted_list[:TOP_N]

def update_metadata(filter_counts):
    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        metadata = {}

    metadata['signals'] = {
        'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        'filter_counts': filter_counts
    }

    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

def main():
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    if today_str in EARLY_CLOSE_DATES and datetime.now(timezone.utc).hour >= EARLY_CLOSE_UTC_HOUR:
        print(f"Early close day — market closed at 1 PM EST. Skipping signals write to prevent garbage data.")
        return

    # Load optionable stocks
    stock_info = load_optionable()
    tickers = list(stock_info.keys())
    print(f"Loaded {len(tickers)} optionable stocks")

    # Fetch all prices in one batch
    raw = fetch_prices(tickers)

    # Parse into usable list
    results, counts = parse_prices(raw, tickers, stock_info)
    print(f"Filter counts: {counts}")

    if not results:
        print("No data returned — market may be closed or API issue")
        return

    # Calculate signals
    top_gainers = filter_top_pct(results, gainers=True)
    top_losers = filter_top_pct(results, gainers=False)
    dollar_gainers = filter_top_dollar(top_gainers, gainers=True)
    dollar_losers = filter_top_dollar(top_losers, gainers=False)

    print(f"Top {TOP_N_PCT} gainers: {[s['ticker'] for s in top_gainers]}")
    print(f"Top {TOP_N_PCT} losers:  {[s['ticker'] for s in top_losers]}")
    print(f"Top {TOP_N} dollar gainers: {[s['ticker'] for s in dollar_gainers]}")
    print(f"Top {TOP_N} dollar losers:  {[s['ticker'] for s in dollar_losers]}")

    # Filter top candidates to those with liquid options — prevents CGON-style no-contract entries
    print("Checking options liquidity on top candidates...")
    def liquid_filter(candidates):
        out = []
        for s in candidates:
            if has_liquid_options(s['ticker'], s['price']):
                out.append(s)
                if len(out) == 1:  # only need #1 per list
                    break
            else:
                print(f"  {s['ticker']} rejected — no liquid contract within budget")
        return out

    dollar_gainers_filtered = liquid_filter(dollar_gainers)
    dollar_losers_filtered  = liquid_filter(dollar_losers)

    # Write signals.json
    signals = {
        'topGainers':    top_gainers,
        'topLosers':     top_losers,
        'dollarGainers': dollar_gainers_filtered if dollar_gainers_filtered else dollar_gainers,
        'dollarLosers':  dollar_losers_filtered  if dollar_losers_filtered  else dollar_losers,
    }

    with open(SIGNALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(signals, f, indent=2)

    print(f"Signals saved to data/signals.json")

    # Update metadata timestamp
    update_metadata(counts)
    print(f"Metadata updated")

if __name__ == '__main__':
    main()
