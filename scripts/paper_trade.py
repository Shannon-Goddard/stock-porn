import yfinance as yf
import json
import os
import math
from datetime import datetime, timezone, timedelta, date

DATA_DIR     = os.path.join(os.path.dirname(__file__), '..', 'data')
SIGNALS_FILE = os.path.join(DATA_DIR, 'signals.json')
TRADES_FILE  = os.path.join(DATA_DIR, 'trades.json')
BLOG_FILE    = os.path.join(DATA_DIR, 'blog.json')

MAX_BUDGET       = 1.00   # max premium per share = $100/contract
MAX_EXP_DAYS     = 7      # quarterly filter — 7-day expiration max
RISK_FREE_RATE   = 0.05

# Macro trigger words for auto_note context
MACRO_TRIGGERS = [
    'fed', 'fomc', 'powell', 'cpi', 'inflation', 'pce',
    'rate hike', 'rate cut', 'war', 'invasion', 'sanctions',
    'china', 'tariff', 'taiwan', 'dxy', 'dollar strength'
]

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def next_trade_id(trades_data):
    if not trades_data['trades']:
        return 1
    return max(t['id'] for t in trades_data['trades']) + 1

def get_spy_change():
    """Get SPY day change % for macro context."""
    try:
        raw = yf.download('SPY', period='2d', interval='1d',
                          auto_adjust=True, progress=False)
        if len(raw) < 2:
            return 0.0
        prev  = float(raw['Close'].iloc[-2].iloc[0]) if hasattr(raw['Close'].iloc[-2], 'iloc') else float(raw['Close'].iloc[-2])
        curr  = float(raw['Close'].iloc[-1].iloc[0]) if hasattr(raw['Close'].iloc[-1], 'iloc') else float(raw['Close'].iloc[-1])
        return round((curr - prev) / prev * 100, 2)
    except Exception:
        return 0.0

def check_macro_active():
    """Scan SPY news for macro trigger words."""
    try:
        t = yf.Ticker('SPY')
        news = t.news or []
        now_utc = datetime.now(timezone.utc)
        cutoff  = now_utc - timedelta(days=3)
        text = ''
        for item in news:
            content = item.get('content', item)
            pub_str = content.get('pubDate', '') or content.get('displayTime', '')
            try:
                pub_dt = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
                if pub_dt > now_utc:
                    pub_dt = now_utc
            except Exception:
                pub_dt = now_utc
            if pub_dt >= cutoff:
                text += ' ' + content.get('title', '').lower()
        found = [kw for kw in MACRO_TRIGGERS if kw in text]
        return bool(found), found
    except Exception:
        return False, []

def get_options_chain(ticker):
    """Return yfinance Ticker object with options data."""
    try:
        return yf.Ticker(ticker)
    except Exception:
        return None

def select_contract(ticker, stock_price, option_type, today):
    """
    Find the best ATM contract within $100 budget expiring within 7 days.
    Returns dict with contract details or None if nothing qualifies.
    option_type: 'CALL' or 'PUT'
    """
    try:
        t = yf.Ticker(ticker)
        expirations = t.options
        if not expirations:
            return None

        # Filter to expirations within MAX_EXP_DAYS
        valid_exps = []
        for exp_str in expirations:
            exp_date = datetime.strptime(exp_str, '%Y-%m-%d').date()
            dte = (exp_date - today).days
            if 0 <= dte <= MAX_EXP_DAYS:
                valid_exps.append((dte, exp_str, exp_date))

        if not valid_exps:
            return None

        # Prefer nearest expiration (most theta-efficient for overnight)
        valid_exps.sort(key=lambda x: x[0])

        for dte, exp_str, exp_date in valid_exps:
            chain = t.option_chain(exp_str)
            df = chain.calls if option_type == 'CALL' else chain.puts

            if df is None or df.empty:
                continue

            # Find strikes closest to ATM within $100 budget
            df = df.copy()
            df['dist'] = abs(df['strike'] - stock_price)
            df = df.sort_values('dist')

            for _, row in df.iterrows():
                strike = float(row['strike'])
                ask    = float(row['ask']) if not math.isnan(float(row['ask'])) else None
                bid    = float(row['bid']) if not math.isnan(float(row['bid'])) else None
                iv     = float(row['impliedVolatility']) if not math.isnan(float(row['impliedVolatility'])) else None

                if ask is None or ask == 0:
                    continue
                if ask > MAX_BUDGET:
                    continue  # exceeds $100/contract budget
                if iv is None or iv == 0:
                    continue

                T = max(dte, 1) / 365  # time to expiration in years

                otm_pct = round((strike - stock_price) / stock_price * 100, 2)
                if option_type == 'PUT':
                    otm_pct = round((stock_price - strike) / stock_price * 100, 2)

                return {
                    'strike':      round(strike, 2),
                    'expiration':  exp_str,
                    'dte':         dte,
                    'T':           round(T, 6),
                    'premium':     round(ask, 4),
                    'cost':        round(ask * 100, 2),
                    'bid':         round(bid, 4) if bid else None,
                    'iv':          round(iv, 4),
                    'spread':      round(ask - bid, 4) if bid else None,
                    'otm_pct':     otm_pct,
                }

        return None

    except Exception as e:
        print(f"  Options chain error for {ticker}: {e}")
        return None

def build_auto_note(signal, option_type, contract, spy_change, macro_active, macro_keywords):
    rank_label = signal.get('_rank', '')
    macro_str  = f"MACRO: {', '.join(macro_keywords)}" if macro_active else "No macro triggers"
    return (
        f"{signal['ticker']} {option_type} | "
        f"${signal['changeDollar']:+.2f} ({signal['changePct']:+.2f}%) | "
        f"{rank_label} | "
        f"Strike ${contract['strike']} exp {contract['expiration']} ({contract['dte']}DTE) | "
        f"IV {round(contract['iv']*100,1)}% | "
        f"SPY {spy_change:+.2f}% | "
        f"{macro_str}"
    )

def build_blog_entry(trade_id, entry):
    return {
        'id':          trade_id,
        'date':        entry['date'],
        'ticker':      entry['ticker'],
        'type':        entry['type'],
        'trade_id':    trade_id,
        'title':       f"{entry['ticker']} {entry['type']} — {entry['date']}",
        'youtube_id':  None,
        'images':      [],
        'published':   True
    }

def process_signal(signal, option_type, rank_label, today, today_str,
                   spy_change, macro_active, macro_keywords, trades_data):
    ticker      = signal['ticker']
    stock_price = signal['price']
    signal['_rank'] = rank_label

    print(f"\n  {ticker} — {option_type} ({rank_label})")
    print(f"  Stock price: ${stock_price} | Change: {signal['changeDollar']:+.2f} ({signal['changePct']:+.2f}%)")

    contract = select_contract(ticker, stock_price, option_type, today)
    if not contract:
        print(f"  No qualifying contract found (budget ${MAX_BUDGET*100:.0f}, {MAX_EXP_DAYS}d max exp)")
        return None

    print(f"  Contract: ${contract['strike']} {option_type} exp {contract['expiration']} "
          f"({contract['dte']}DTE) @ ${contract['premium']} | IV {round(contract['iv']*100,1)}%")

    auto_note = build_auto_note(signal, option_type, contract,
                                spy_change, macro_active, macro_keywords)

    trade_id = next_trade_id(trades_data)

    trade = {
        'id':     trade_id,
        'status': 'open',
        'entry': {
            'date':                today_str,
            'time':                '15:55 PST',
            'ticker':              ticker,
            'name':                signal['name'],
            'sector':              signal['sector'],
            'type':                option_type,
            'strike':              contract['strike'],
            'expiration':          contract['expiration'],
            'dte_at_entry':        contract['dte'],
            'T_at_entry':          contract['T'],
            'stock_price_at_entry': stock_price,
            'premium':             contract['premium'],
            'cost':                contract['cost'],
            'bid':                 contract['bid'],
            'spread':              contract['spread'],
            'iv_at_entry':         contract['iv'],
            'otm_pct':             contract['otm_pct'],
            'signal_rank':         rank_label,
            'signal_pct':          signal['changePct'],
            'signal_dollar':       signal['changeDollar'],
            'spy_change':          spy_change,
            'macro_active':        macro_active,
            'macro_keywords':      macro_keywords,
            'auto_note':           auto_note
        },
        'news_scan': None,
        'exit':      None,
        'fomo':      None
    }

    # Update first_trade_date if this is the first ever trade
    if trades_data['first_trade_date'] is None:
        trades_data['first_trade_date'] = today_str

    trades_data['trades'].append(trade)
    # Deduct cost from balance
    print(f"  Trade #{trade_id} logged.")
    return trade_id

def main():
    today     = date.today()
    today_str = today.strftime('%Y-%m-%d')
    print(f"paper_trade.py — {today_str} 15:55 PST")

    signals     = load_json(SIGNALS_FILE)
    trades_data = load_json(TRADES_FILE)
    blog        = load_json(BLOG_FILE)

    # Check for existing open trades — don't double-enter on same day
    open_today = [t for t in trades_data['trades']
                  if t['status'] == 'open' and t['entry']['date'] == today_str]
    if open_today:
        print(f"Already have {len(open_today)} open trade(s) from today — skipping entry")
        return

    print("\nFetching SPY change and macro context...")
    spy_change                  = get_spy_change()
    macro_active, macro_keywords = check_macro_active()
    print(f"SPY: {spy_change:+.2f}% | Macro active: {macro_active} {macro_keywords}")

    # Select candidates:
    # Contract 1 — top dollar gainer → CALL (overnight fade candidate)
    # Contract 2 — top dollar loser  → PUT  (overnight bounce candidate)
    candidates = []
    if signals.get('dollarGainers'):
        candidates.append((signals['dollarGainers'][0], 'CALL', 'dollar_gainer_1'))
    if signals.get('dollarLosers'):
        candidates.append((signals['dollarLosers'][0], 'PUT', 'dollar_loser_1'))

    print(f"\nProcessing {len(candidates)} candidate(s)...")
    new_trade_ids = []

    for signal, option_type, rank_label in candidates:
        trade_id = process_signal(
            signal, option_type, rank_label, today, today_str,
            spy_change, macro_active, macro_keywords, trades_data
        )
        if trade_id:
            new_trade_ids.append(trade_id)
            # Add blog skeleton entry
            trade = next(t for t in trades_data['trades'] if t['id'] == trade_id)
            blog.append(build_blog_entry(trade_id, trade['entry']))

    if not new_trade_ids:
        print("\nNo trades entered today — no qualifying contracts found")
        return

    save_json(TRADES_FILE, trades_data)
    save_json(BLOG_FILE, blog)
    print(f"\nDone. {len(new_trade_ids)} trade(s) entered: {new_trade_ids}")

if __name__ == '__main__':
    main()
