import yfinance as yf
import json
import os
import math
from datetime import datetime, timezone, timedelta

DATA_DIR    = os.path.join(os.path.dirname(__file__), '..', 'data')
TRADES_FILE = os.path.join(DATA_DIR, 'trades.json')
CANDLES_DIR = os.path.join(DATA_DIR, 'candles')

# PST timezone offset (UTC-8 standard, UTC-7 daylight — use fixed for simplicity)
PST_OFFSET = timedelta(hours=-8)

BULLISH_KEYWORDS = [
    'beat expectations', 'beats expectations', 'raised guidance', 'raises guidance',
    'new contract', 'fda approval', 'fda approved', 'partnership announced',
    'share buyback', 'buyback', 'dividend increase', 'record revenue',
    'expanding into', 'strategic acquisition', 'upgrade', 'upgraded',
    'strong earnings', 'profit rises', 'revenue growth', 'raised outlook',
    'positive', 'surge', 'soars', 'jumps', 'rallies', 'breakthrough'
]

BEARISH_KEYWORDS = [
    'missed expectations', 'misses expectations', 'lowered guidance', 'lowers guidance',
    'investigation', 'recall', 'ceo resigned', 'ceo resigns', 'sec inquiry',
    'sec investigation', 'delayed launch', 'restructuring', 'layoffs', 'layoff',
    'debt downgrade', 'downgrade', 'downgraded', 'missed earnings', 'misses earnings',
    'revenue decline', 'loss widens', 'warning', 'concern', 'falls', 'drops',
    'plunges', 'tumbles', 'disappoints', 'weak', 'cuts forecast'
]

def load_trades():
    with open(TRADES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_trades(data):
    with open(TRADES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def get_open_trades(trades_data):
    return [t for t in trades_data['trades'] if t['status'] == 'open']

def score_headlines(headlines, ticker):
    """Score a list of headline strings. Returns sentiment + keywords found."""
    text = ' '.join(headlines).lower()
    bullish_found = [kw for kw in BULLISH_KEYWORDS if kw in text]
    bearish_found = [kw for kw in BEARISH_KEYWORDS if kw in text]
    score = len(bullish_found) - len(bearish_found)
    if score > 0:   sentiment = 'bullish'
    elif score < 0: sentiment = 'bearish'
    else:           sentiment = 'neutral'
    return sentiment, bullish_found + bearish_found

def fetch_news_for_ticker(ticker):
    """Fetch Yahoo Finance news headlines for a ticker.
    Includes articles from last 3 days to handle weekends + Yahoo date quirks."""
    try:
        t = yf.Ticker(ticker)
        news = t.news or []
        now_utc = datetime.now(timezone.utc)
        cutoff  = now_utc - timedelta(days=3)
        headlines = []
        for item in news:
            content = item.get('content', item)
            title   = content.get('title', '')
            pub_str = content.get('pubDate', '') or content.get('displayTime', '')
            try:
                pub_dt = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
                # Yahoo sometimes returns future timestamps — treat those as today
                if pub_dt > now_utc:
                    pub_dt = now_utc
            except Exception:
                pub_dt = now_utc
            if pub_dt >= cutoff and title:
                headlines.append(title)
        return headlines
    except Exception as e:
        print(f"  News fetch failed for {ticker}: {e}")
        return []

def days_since_last_scan(trade):
    """How many days since the entry date — handles weekend gaps."""
    entry_date = datetime.strptime(trade['entry']['date'], '%Y-%m-%d').date()
    today = datetime.now(timezone.utc).date()
    return (today - entry_date).days

def fetch_candles(ticker, date_str):
    """Fetch 1-min candles for ticker on a given date, save to candles/."""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period='1d', interval='1m')
        if df is None or df.empty:
            print(f"  No candle data for {ticker}")
            return
        candles = []
        for ts, row in df.iterrows():
            candles.append({
                'time':   str(ts),
                'open':   round(float(row['Open']), 4),
                'high':   round(float(row['High']), 4),
                'low':    round(float(row['Low']), 4),
                'close':  round(float(row['Close']), 4),
                'volume': int(row['Volume'])
            })
        out_path = os.path.join(CANDLES_DIR, f"{ticker}_{date_str}.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(candles, f)
        print(f"  Candles saved: {ticker}_{date_str}.json ({len(candles)} bars)")
    except Exception as e:
        print(f"  Candle fetch failed for {ticker}: {e}")

def make_decision(ticker_sentiment, spy_sentiment, spx_sentiment, trade_type):
    """
    Determine hold or sell based on news sentiment vs trade direction.
    PUT thesis confirmed by bearish news. CALL thesis confirmed by bullish news.
    """
    if trade_type == 'PUT':
        confirmed = ticker_sentiment == 'bearish' or spy_sentiment == 'bearish'
    else:
        confirmed = ticker_sentiment == 'bullish' or spy_sentiment == 'bullish'

    if confirmed:
        return 'hold', f"{ticker_sentiment} keywords confirmed {trade_type} thesis"
    return 'sell', f"no confirmation for {trade_type} thesis — sell at open"

def main():
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    now_pst   = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S PST')
    print(f"fetch_news.py — {now_pst}")

    data = load_trades()
    open_trades = get_open_trades(data)

    if not open_trades:
        print("No open trades — nothing to scan")
        return

    print(f"Open trades: {[t['entry']['ticker'] for t in open_trades]}")

    # Always scan SPY and SPX for macro context
    print("\nScanning SPY...")
    spy_headlines = fetch_news_for_ticker('SPY')
    spy_sentiment, spy_keywords = score_headlines(spy_headlines, 'SPY')
    print(f"  SPY: {spy_sentiment} | keywords: {spy_keywords}")

    print("Scanning SPX...")
    spx_headlines = fetch_news_for_ticker('^GSPC')
    spx_sentiment, spx_keywords = score_headlines(spx_headlines, 'SPX')
    print(f"  SPX: {spx_sentiment} | keywords: {spx_keywords}")

    for trade in open_trades:
        ticker = trade['entry']['ticker']
        trade_type = trade['entry']['type']
        gap_days = days_since_last_scan(trade)
        print(f"\nScanning {ticker} (gap: {gap_days} days)...")

        headlines = fetch_news_for_ticker(ticker)
        ticker_sentiment, keywords_found = score_headlines(headlines, ticker)
        print(f"  {ticker}: {ticker_sentiment} | keywords: {keywords_found}")

        decision, reason = make_decision(
            ticker_sentiment, spy_sentiment, spx_sentiment, trade_type
        )
        print(f"  Decision: {decision.upper()} — {reason}")

        # Fetch and store today's 1-min candles
        print(f"  Fetching candles for {ticker}...")
        fetch_candles(ticker, today_str)

        # Log news scan result to trade
        trade['news_scan'] = {
            'scanned_at':       now_pst,
            'gap_days':         gap_days,
            'ticker_sentiment': ticker_sentiment,
            'spy_sentiment':    spy_sentiment,
            'spx_sentiment':    spx_sentiment,
            'keywords_found':   keywords_found,
            'spy_keywords':     spy_keywords,
            'spx_keywords':     spx_keywords,
            'decision':         decision,
            'decision_reason':  reason
        }

    save_trades(data)
    print(f"\nNews scan complete — trades.json updated")

if __name__ == '__main__':
    main()
