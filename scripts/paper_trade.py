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
MIN_DTE          = 1      # 0DTE at 3:55 PM = ~35 min left, not an overnight hold
MAX_OTM_1DTE     = 20.0   # 1DTE contracts: reject if strike >20% OTM
MAX_OTM_GENERAL  = 10.0   # 2DTE+: reject if strike >10% OTM — outside expected move
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
            return None
        prev  = float(raw['Close'].iloc[-2].iloc[0]) if hasattr(raw['Close'].iloc[-2], 'iloc') else float(raw['Close'].iloc[-2])
        curr  = float(raw['Close'].iloc[-1].iloc[0]) if hasattr(raw['Close'].iloc[-1], 'iloc') else float(raw['Close'].iloc[-1])
        if math.isnan(prev) or math.isnan(curr) or prev == 0:
            return None
        return round((curr - prev) / prev * 100, 2)
    except Exception:
        return None

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
            if dte < MIN_DTE:
                continue  # 0DTE at 3:55 PM = lottery ticket with a 35-min fuse
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

                # 1DTE deep OTM filter
                if dte == 1 and otm_pct > MAX_OTM_1DTE:
                    continue
                # General OTM filter for 2DTE+ — strike outside expected move range
                if dte >= 2 and otm_pct > MAX_OTM_GENERAL:
                    continue

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

def calc_expected_move(stock_price, strike, iv, T, option_type):
    """
    1σ expected move = stock_price × IV × sqrt(T)
    Returns dict with one_sigma_pct, upper, lower, strike_position.
    strike_position: inside / at_edge (within 2% of boundary) / outside
    """
    one_sigma_pct = round(iv * math.sqrt(T) * 100, 2)
    upper = round(stock_price * (1 + iv * math.sqrt(T)), 2)
    lower = round(stock_price * (1 - iv * math.sqrt(T)), 2)

    # Is the strike inside, at the edge, or outside the expected move range?
    edge_buffer = stock_price * 0.02  # 2% buffer defines "at_edge"
    if option_type == 'CALL':
        dist = strike - upper
    else:
        dist = lower - strike

    if dist <= 0:
        position = 'inside'
    elif dist <= edge_buffer:
        position = 'at_edge'
    else:
        position = 'outside'

    return {
        'one_sigma_pct': one_sigma_pct,
        'upper':         upper,
        'lower':         lower,
        'strike_position': position
    }

def build_auto_note(
        signal, option_type, contract, spy_change, macro_active, macro_keywords):
    rank_label = signal.get('_rank', '')
    macro_str  = f"MACRO: {', '.join(macro_keywords)}" if macro_active else "No macro triggers"
    spy_str = f"SPY {spy_change:+.2f}%" if spy_change is not None else "SPY n/a"
    return (
        f"{signal['ticker']} {option_type} | "
        f"${signal['changeDollar']:+.2f} ({signal['changePct']:+.2f}%) | "
        f"{rank_label} | "
        f"Strike ${contract['strike']} exp {contract['expiration']} ({contract['dte']}DTE) | "
        f"IV {round(contract['iv']*100,1)}% | "
        f"{spy_str} | "
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

METADATA_FILE = os.path.join(DATA_DIR, 'metadata.json')

import sys
sys.path.insert(0, os.path.dirname(__file__))
try:
    from fetch_signals import SECTOR_ETF_MAP
except ImportError:
    SECTOR_ETF_MAP = {}

# US market holidays 2026-2027 (NYSE observed dates)
MARKET_HOLIDAYS = {
    '2026-01-01', '2026-01-19', '2026-02-16', '2026-04-03',
    '2026-05-25', '2026-07-03', '2026-09-07', '2026-11-26', '2026-12-25',
    '2027-01-01', '2027-01-18', '2027-02-15', '2027-04-02',
    '2027-05-31', '2027-07-05', '2027-09-06', '2027-11-25', '2027-12-24',
}

# NYSE early close days — market closes 1 PM EST (21:00 UTC)
# 3:55 PM PST cron fires at 23:55 UTC — after close, do not trade
EARLY_CLOSE_DATES = {
    # 2025
    '2025-11-28',  # day after Thanksgiving
    '2025-12-24',  # Christmas Eve
    # 2026
    '2026-11-27',  # day after Thanksgiving
    '2026-12-24',  # Christmas Eve (also a holiday — belt+suspenders)
    # 2027
    '2027-11-26',  # day after Thanksgiving
    '2027-12-24',  # Christmas Eve
}
EARLY_CLOSE_UTC_HOUR = 21  # 1 PM EST = 21:00 UTC


def get_entry_context(ticker, stock_price, sector):
    """
    Collect safety-net fields at entry time.
    iv_rank           — where today's IV sits relative to 60d realized vol range (0-1 proxy)
    volume_ratio      — today's volume vs 30-day avg (unusual activity flag)
    sector_etf_change — sector ETF % change today (is the trade fighting the sector?)
    All fields nullable — never block a trade if lookup fails.
    """
    ctx = {'iv_rank': None, 'volume_ratio': None, 'sector_etf_change': None, 'sector_etf': None}
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period='60d', interval='1d')
        if hist is not None and len(hist) >= 20:
            avg_vol = float(hist['Volume'].iloc[-30:].mean())
            today_vol = float(hist['Volume'].iloc[-1])
            if avg_vol > 0:
                ctx['volume_ratio'] = round(today_vol / avg_vol, 2)
            try:
                exps = t.options
                if exps:
                    chain = t.option_chain(exps[0])
                    near = chain.calls[abs(chain.calls['strike'] - stock_price) < stock_price * 0.1]
                    if not near.empty:
                        iv_sample = float(near['impliedVolatility'].median())
                        hv_series = [
                            float(hist['Close'].iloc[max(0, i-20):i].pct_change().dropna().std() * math.sqrt(252))
                            for i in range(20, len(hist))
                        ]
                        if hv_series:
                            hv_min, hv_max = min(hv_series), max(hv_series)
                            if hv_max > hv_min:
                                ctx['iv_rank'] = round((iv_sample - hv_min) / (hv_max - hv_min), 3)
            except Exception:
                pass
    except Exception:
        pass

    sector_etf = SECTOR_ETF_MAP.get(sector)
    ctx['sector_etf'] = sector_etf
    if sector_etf:
        try:
            raw = yf.download(sector_etf, period='2d', interval='1d', auto_adjust=True, progress=False)
            if len(raw) >= 2:
                prev = float(raw['Close'].iloc[-2].iloc[0]) if hasattr(raw['Close'].iloc[-2], 'iloc') else float(raw['Close'].iloc[-2])
                curr = float(raw['Close'].iloc[-1].iloc[0]) if hasattr(raw['Close'].iloc[-1], 'iloc') else float(raw['Close'].iloc[-1])
                if prev > 0:
                    ctx['sector_etf_change'] = round((curr - prev) / prev * 100, 2)
        except Exception:
            pass

    return ctx


def process_signal(signal, option_type, rank_label, today, today_str,
                   spy_change, macro_active, macro_keywords, trades_data):
    ticker      = signal['ticker']
    stock_price = signal['price']
    signal['_rank'] = rank_label

    print(f"\n  {ticker} — {option_type} ({rank_label})")
    print(f"  Stock price: ${stock_price} | Change: {signal['changeDollar']:+.2f} ({signal['changePct']:+.2f}%)")

    # Safety-net context fields
    print(f"  Fetching entry context (iv_rank, volume_ratio, sector_etf_change)...")
    entry_ctx = get_entry_context(ticker, stock_price, signal.get('sector', ''))

    contract = select_contract(ticker, stock_price, option_type, today)
    if not contract:
        print(f"  No qualifying contract found (budget ${MAX_BUDGET*100:.0f}, {MAX_EXP_DAYS}d max exp)")
        return None

    print(f"  iv_rank: {entry_ctx['iv_rank']} | volume_ratio: {entry_ctx['volume_ratio']} | "
          f"sector_etf: {entry_ctx['sector_etf']} {entry_ctx['sector_etf_change']:+.2f}%" if entry_ctx['sector_etf_change'] is not None
          else f"  iv_rank: {entry_ctx['iv_rank']} | volume_ratio: {entry_ctx['volume_ratio']} | sector_etf: {entry_ctx['sector_etf']} n/a")

    print(f"  Contract: ${contract['strike']} {option_type} exp {contract['expiration']} "
          f"({contract['dte']}DTE) @ ${contract['premium']} | IV {round(contract['iv']*100,1)}%")

    auto_note = build_auto_note(signal, option_type, contract,
                                spy_change, macro_active, macro_keywords)

    expected_move = calc_expected_move(
        stock_price, contract['strike'], contract['iv'], contract['T'], option_type
    )
    print(f"  Expected move: ±{expected_move['one_sigma_pct']}% "
          f"[${expected_move['lower']} – ${expected_move['upper']}] "
          f"| Strike position: {expected_move['strike_position']}")

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
            'expected_move':       expected_move,
            'signal_rank':         rank_label,
            'signal_pct':          signal['changePct'],
            'signal_dollar':       signal['changeDollar'],
            'signal_first_appeared': signal.get('signal_first_appeared'),
            'spy_change':          spy_change if spy_change is not None and not math.isnan(spy_change) else None,
            'macro_active':        macro_active,
            'macro_keywords':      macro_keywords,
            'iv_rank':             entry_ctx['iv_rank'],
            'volume_ratio':        entry_ctx['volume_ratio'],
            'sector_etf':          entry_ctx['sector_etf'],
            'sector_etf_change':   entry_ctx['sector_etf_change'],
            'auto_note':           auto_note
        },
        'news_scan':  None,
        'exit':       None,
        'fomo':       None,
        'post_mortem': None,
        'ai_notes':   None   # reserved — AI-assisted analysis layer (future)
    }

    # Update first_trade_date if this is the first ever trade
    if trades_data['first_trade_date'] is None:
        trades_data['first_trade_date'] = today_str

    trades_data['trades'].append(trade)
    # Deduct cost from balance
    print(f"  Trade #{trade_id} logged.")
    return trade_id

def check_no_trade(spy_change, signals):
    """
    NO TRADE signal — highest-confidence call is sometimes not trading.
    Returns (skip, reason) if conditions warrant skipping today.
    Conditions:
    - SPY moved > 3% in either direction (extreme day, IV elevated across board)
    - No dollar gainers or losers in signals (market flat, no signal)
    """
    if spy_change is not None and abs(spy_change) > 3.0:
        return True, f"NO TRADE: SPY moved {spy_change:+.2f}% — extreme day, IV elevated across board, premium too expensive"
    if not signals.get('dollarGainers') and not signals.get('dollarLosers'):
        return True, "NO TRADE: no dollar movers in signals — market flat, no tradeable signal"
    return False, None


def main():
    today     = date.today()
    today_str = today.strftime('%Y-%m-%d')
    print(f"paper_trade.py — {today_str} 15:55 PST")

    if today_str in MARKET_HOLIDAYS:
        print(f"Market holiday — {today_str} is a NYSE observed holiday. No trade today.")
        return

    if today_str in EARLY_CLOSE_DATES:
        now_utc_hour = datetime.now(timezone.utc).hour
        if now_utc_hour >= EARLY_CLOSE_UTC_HOUR:
            print(f"Early close day — market closed at 1 PM EST. Cron fired after close. No trade today.")
            return

    signals     = load_json(SIGNALS_FILE)
    trades_data = load_json(TRADES_FILE)
    blog        = load_json(BLOG_FILE)
    metadata    = load_json(METADATA_FILE)

    # Check for existing open trades — don't double-enter on same day
    open_today = [t for t in trades_data['trades']
                  if t['status'] == 'open' and t['entry']['date'] == today_str]
    if open_today:
        print(f"Already have {len(open_today)} open trade(s) from today — skipping entry")
        return

    print("\nFetching SPY change and macro context...")
    spy_change                  = get_spy_change()
    macro_active, macro_keywords = check_macro_active()
    spy_str = f"{spy_change:+.2f}%" if spy_change is not None else "n/a"
    print(f"SPY: {spy_str} | Macro active: {macro_active} {macro_keywords}")

    skip, skip_reason = check_no_trade(spy_change, signals)
    if skip:
        print(f"\n{skip_reason}")
        metadata['paper_trade_entry'] = {
            'date':           today_str,
            'trades_entered': [],
            'skipped':        [],
            'no_trade':       skip_reason
        }
        save_json(METADATA_FILE, metadata)
        return


    # Select candidates:
    # Contract 1 — top dollar gainer → PUT  (fade the move — expect reversal overnight)
    # Contract 2 — top dollar loser  → CALL (fade the move — expect bounce overnight)
    candidates = []
    if signals.get('dollarGainers'):
        candidates.append((signals['dollarGainers'][0], 'PUT', 'dollar_gainer_1'))
    if signals.get('dollarLosers'):
        candidates.append((signals['dollarLosers'][0], 'CALL', 'dollar_loser_1'))

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

    # Log entry summary to metadata for front-end display
    skipped = []
    for signal, option_type, rank_label in candidates:
        tid = next((i for i in new_trade_ids
                    if any(t['id'] == i and t['entry']['ticker'] == signal['ticker']
                           for t in trades_data['trades'])), None)
        if tid is None:
            skipped.append({
                'ticker':      signal['ticker'],
                'type':        option_type,
                'rank':        rank_label,
                'reason':      'no qualifying contract (budget $100, 7d max expiry, OTM filter)'
            })
    metadata['paper_trade_entry'] = {
        'date':          today_str,
        'trades_entered': new_trade_ids,
        'skipped':        skipped
    }
    save_json(METADATA_FILE, metadata)

    if not new_trade_ids:
        print("\nNo trades entered today — no qualifying contracts found")
        save_json(TRADES_FILE, trades_data)
        save_json(BLOG_FILE, blog)
        return

    save_json(TRADES_FILE, trades_data)
    save_json(BLOG_FILE, blog)
    print(f"\nDone. {len(new_trade_ids)} trade(s) entered: {new_trade_ids}")

if __name__ == '__main__':
    main()
