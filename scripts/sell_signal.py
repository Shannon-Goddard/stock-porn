import yfinance as yf
import json
import os
import math
from datetime import datetime, timezone, date, timedelta

DATA_DIR     = os.path.join(os.path.dirname(__file__), '..', 'data')
TRADES_FILE  = os.path.join(DATA_DIR, 'trades.json')
STATS_FILE   = os.path.join(DATA_DIR, 'stats.json')
BLOG_FILE    = os.path.join(DATA_DIR, 'blog.json')
CANDLES_DIR  = os.path.join(DATA_DIR, 'candles')

RISK_FREE_RATE = 0.05

# ── Black-Scholes (inline to avoid import path issues in Actions) ─────────────
from scipy.stats import norm

def _d1(S, K, T, r, sigma):
    return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

def _bs_price(option_type, S, K, T, r, sigma):
    if T <= 0:
        return max(0.0, S - K) if option_type == 'CALL' else max(0.0, K - S)
    d1 = _d1(S, K, T, r, sigma)
    d2 = d1 - sigma * math.sqrt(T)
    if option_type == 'CALL':
        return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def _theta_per_min(option_type, S, K, T, r, sigma):
    """Theta per trading minute per contract ($)."""
    if T <= 0:
        return 0.0
    d1 = _d1(S, K, T, r, sigma)
    d2 = d1 - sigma * math.sqrt(T)
    pdf_d1 = norm.pdf(d1)
    common = -(S * pdf_d1 * sigma) / (2 * math.sqrt(T))
    if option_type == 'CALL':
        t = common - r * K * math.exp(-r * T) * norm.cdf(d2)
    else:
        t = common + r * K * math.exp(-r * T) * norm.cdf(-d2)
    return round((t / 365 / 390) * 100, 6)  # per contract per minute

# ─────────────────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def get_intraday_candles(ticker, today_str):
    """Load saved candles if available, otherwise fetch live."""
    candle_path = os.path.join(CANDLES_DIR, f"{ticker}_{today_str}.json")
    if os.path.exists(candle_path):
        with open(candle_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    try:
        t = yf.Ticker(ticker)
        df = t.history(period='1d', interval='1m')
        if df is None or df.empty:
            return []
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
        with open(candle_path, 'w', encoding='utf-8') as f:
            json.dump(candles, f)
        return candles
    except Exception as e:
        print(f"  Candle fetch failed for {ticker}: {e}")
        return []

def get_open_price(candles):
    if not candles:
        return None, None
    return candles[0]['open'], candles[0]['time']

def get_second_candle_price(candles):
    if len(candles) < 2:
        return candles[0]['close'] if candles else None, None
    return candles[1]['open'], candles[1]['time']

def get_day_high_low(candles, window_minutes=30):
    """Return high/low within first window_minutes after open."""
    if not candles:
        return None, None, None, None
    window = candles[:window_minutes] if len(candles) >= window_minutes else candles
    high_candle = max(window, key=lambda c: c['high'])
    low_candle  = min(window, key=lambda c: c['low'])
    return (
        high_candle['high'], high_candle['time'],
        low_candle['low'],   low_candle['time']
    )

def minutes_to_candle(candles, target_time_str):
    if not candles or not target_time_str:
        return 0
    try:
        open_dt   = datetime.fromisoformat(candles[0]['time'].split('+')[0].split('-0')[0])
        target_dt = datetime.fromisoformat(target_time_str.split('+')[0].split('-0')[0])
        return max(0, int((target_dt - open_dt).total_seconds() / 60))
    except Exception:
        return 0

def calc_fomo(trade, candles, sell_option_price, sell_time):
    """
    Run Black-Scholes FOMO calculation.
    sell_option_price = BS per-share value at sell time (NOT stock price).
    """
    entry       = trade['entry']
    option_type = entry['type']
    K           = entry['strike']
    T_entry     = entry['T_at_entry']
    sigma       = entry['iv_at_entry']
    dte         = entry['dte_at_entry']
    cost        = entry['cost']
    r           = RISK_FREE_RATE

    # Sell value — option price per share × 100 = contract value
    sell_contract_value = round(sell_option_price * 100, 2)
    sell_pnl            = round(sell_contract_value - cost, 2)

    sell_mins      = minutes_to_candle(candles, sell_time) if candles else 2
    T_at_sell      = max(T_entry - (sell_mins / (390 * 365)), 0)
    theta_per_min  = _theta_per_min(option_type, entry['stock_price_at_entry'], K, T_entry, r, sigma)
    theta_burned   = round(theta_per_min * sell_mins, 2)

    day_high, high_time, day_low, low_time = get_day_high_low(candles)

    fomo = {
        'sell_contract_value':  sell_contract_value,
        'sell_pnl':             sell_pnl,
        'theta_burned_at_sell': theta_burned,
        'theta_per_min':        theta_per_min,
    }

    if day_high and day_low:
        high_mins = minutes_to_candle(candles, high_time)
        low_mins  = minutes_to_candle(candles, low_time)

        T_at_high = max(T_entry - (high_mins / (390 * 365)), 0)
        T_at_low  = max(T_entry - (low_mins  / (390 * 365)), 0)

        bs_at_high = _bs_price(option_type, day_high, K, T_at_high, r, sigma)
        bs_at_low  = _bs_price(option_type, day_low,  K, T_at_low,  r, sigma)

        contract_at_high = round(bs_at_high * 100, 2)
        contract_at_low  = round(bs_at_low  * 100, 2)

        if option_type == 'CALL':
            best_value, worst_value = contract_at_high, contract_at_low
            best_time,  worst_time  = high_time, low_time
        else:
            best_value, worst_value = contract_at_low, contract_at_high
            best_time,  worst_time  = low_time, high_time

        best_pnl      = round(best_value  - cost, 2)
        worst_pnl     = round(worst_value - cost, 2)
        left_on_table = round(best_pnl - sell_pnl, 2)

        if dte == 0:
            tnote = f"0DTE: Theta burned est. ${abs(theta_burned):.2f} by sell time — 0DTE decay is violent"
        elif dte == 1:
            tnote = f"1DTE: Theta moderate at open, accelerating by noon. Est. ${abs(theta_burned):.2f} burned"
        else:
            tnote = f"{dte}DTE: Theta minimal at open, stock direction dominates. Est. ${abs(theta_burned):.2f} burned"

        fomo.update({
            'day_high': {
                'stock_price':       day_high,
                'time':              high_time,
                'bs_contract_value': contract_at_high,
                'theoretical_pnl':   round(contract_at_high - cost, 2)
            },
            'day_low': {
                'stock_price':       day_low,
                'time':              low_time,
                'bs_contract_value': contract_at_low,
                'theoretical_pnl':   round(contract_at_low - cost, 2)
            },
            'best_case':      {'value': best_value,  'pnl': best_pnl,  'time': best_time},
            'worst_case':     {'value': worst_value, 'pnl': worst_pnl, 'time': worst_time},
            'left_on_table':  left_on_table,
            'theta_note':     tnote,
        })

    return fomo

def update_stats(stats, trade, excluded_ids):
    """Recalculate all stats after a trade closes."""
    entry  = trade['entry']
    exit_  = trade['exit']
    fomo   = trade['fomo']
    news   = trade['news_scan']
    pnl    = exit_['pnl']
    won    = pnl > 0
    is_excluded = trade['id'] in excluded_ids

    stats['last_updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

    # Overall — always update (raw all-time numbers)
    o = stats['overall']
    o['total_trades'] += 1
    if won: o['wins'] += 1
    else:   o['losses'] += 1
    o['win_rate']        = round(o['wins'] / o['total_trades'] * 100, 1)
    o['total_pnl']       = round(o['total_pnl'] + pnl, 2)
    o['avg_pnl']         = round(o['total_pnl'] / o['total_trades'], 2)
    o['current_balance'] = round(o['total_pnl'], 2)

    # clean_balance — excludes flagged trades
    if not is_excluded:
        stats['clean_balance'] = round(stats.get('clean_balance', 0.0) + pnl, 2)

    # Skip hypothesis + analytics buckets for excluded trades
    if is_excluded:
        return

    # By day of week
    entry_date = datetime.strptime(entry['date'], '%Y-%m-%d')
    day_name   = entry_date.strftime('%A')
    d = stats['by_day_of_week'][day_name]
    d['trades'] += 1
    if won: d['wins'] += 1
    d['avg_pnl'] = round((d['avg_pnl'] * (d['trades'] - 1) + pnl) / d['trades'], 2)

    # By sector
    sector = entry['sector']
    if sector not in stats['by_sector']:
        stats['by_sector'][sector] = {'trades': 0, 'wins': 0, 'avg_pnl': 0.0}
    s = stats['by_sector'][sector]
    s['trades'] += 1
    if won: s['wins'] += 1
    s['avg_pnl'] = round((s['avg_pnl'] * (s['trades'] - 1) + pnl) / s['trades'], 2)

    # By signal rank
    rank = entry['signal_rank']
    if rank not in stats['by_signal_rank']:
        stats['by_signal_rank'][rank] = {'trades': 0, 'wins': 0, 'avg_pnl': 0.0}
    sr = stats['by_signal_rank'][rank]
    sr['trades'] += 1
    if won: sr['wins'] += 1
    sr['avg_pnl'] = round((sr['avg_pnl'] * (sr['trades'] - 1) + pnl) / sr['trades'], 2)

    # SPY correlation
    spy_up = entry['spy_change'] >= 0
    sc = stats['spy_correlation']['spy_up_days' if spy_up else 'spy_down_days']
    sc['trades'] += 1
    if won and entry['type'] == 'PUT':  sc['put_wins']  += 1
    if won and entry['type'] == 'CALL': sc['call_wins'] += 1

    # FOMO
    if fomo:
        left = fomo.get('left_on_table', 0)
        f = stats['fomo']
        clean_count = sum(
            1 for t in [trade] if t['id'] not in excluded_ids
        )
        n_fomo = f['sell_at_open_trades'] + f['hold_2min_trades'] + 1
        f['avg_left_on_table'] = round(
            (f['avg_left_on_table'] * (n_fomo - 1) + left) / n_fomo, 2
        )
        trigger = exit_.get('sell_trigger', 'sell_at_open')
        if trigger == 'hold_2min':
            f['hold_2min_trades'] += 1
            n = f['hold_2min_trades']
            f['hold_2min_avg_pnl'] = round(
                (f['hold_2min_avg_pnl'] * (n - 1) + pnl) / n, 2
            )
        else:
            f['sell_at_open_trades'] += 1
            n = f['sell_at_open_trades']
            f['sell_at_open_avg_pnl'] = round(
                (f['sell_at_open_avg_pnl'] * (n - 1) + pnl) / n, 2
            )

    # IV crush
    iv_entry = entry.get('iv_at_entry')
    if iv_entry:
        ic = stats['iv_crush']
        ic['samples'] += 1
        n = ic['samples']
        ic['avg_iv_at_entry'] = round(
            (ic['avg_iv_at_entry'] * (n - 1) + iv_entry) / n, 4
        )

    # Keyword accuracy
    if news:
        decision  = news.get('decision', 'sell')
        sentiment = news.get('ticker_sentiment', 'neutral')
        correct   = (decision == 'hold' and won) or (decision == 'sell' and not won)
        ka = stats['keyword_accuracy'][sentiment]
        ka['fired'] += 1
        if correct: ka['correct'] += 1
        kl = stats['methodology_score']['keyword_layer']
        kl['predictions'] += 1
        if correct: kl['correct'] += 1

    # Methodology score — SPY layer
    spy_layer_correct = (
        (entry['spy_change'] < 0 and entry['type'] == 'PUT'  and won) or
        (entry['spy_change'] > 0 and entry['type'] == 'CALL' and won)
    )
    sl = stats['methodology_score']['spy_layer']
    sl['predictions'] += 1
    if spy_layer_correct: sl['correct'] += 1

    # ── Hypotheses ────────────────────────────────────────────────────────────
    h = stats.get('hypotheses', {})

    # 1. Strike position vs expected move
    strike_pos = entry.get('expected_move', {}).get('strike_position')
    if strike_pos and 'strike_inside_expected_move' in h:
        bucket = h['strike_inside_expected_move']['buckets'].get(strike_pos)
        if bucket is not None:
            bucket['trades'] += 1
            if won: bucket['wins'] += 1

    # 2. Gap direction vs thesis
    gap_dir = exit_.get('gap_direction')
    if gap_dir and 'gap_with_thesis' in h:
        bucket = h['gap_with_thesis']['buckets'].get(gap_dir)
        if bucket is not None:
            bucket['trades'] += 1
            if won: bucket['wins'] += 1

    # 3. Macro keyword performance
    if entry.get('macro_active') and entry.get('macro_keywords'):
        mkp = h.get('macro_keyword_performance', {}).get('buckets', {})
        for kw in entry['macro_keywords']:
            if kw not in mkp:
                mkp[kw] = {'trades': 0, 'wins': 0}
            mkp[kw]['trades'] += 1
            if won: mkp[kw]['wins'] += 1

    # 4. DTE performance
    dte = entry.get('dte_at_entry', 0)
    if 'dte_performance' in h:
        if dte == 1:
            dte_key = '1dte'
        elif dte in (2, 3):
            dte_key = '2_3dte'
        else:
            dte_key = '4dte_plus'
        bucket = h['dte_performance']['buckets'].get(dte_key)
        if bucket is not None:
            bucket['trades'] += 1
            if won: bucket['wins'] += 1

def update_blog(blog, trade):
    entry  = trade['entry']
    exit_  = trade['exit']
    fomo   = trade['fomo']
    news   = trade['news_scan']
    pnl    = exit_['pnl']
    won    = pnl > 0

    result_word = 'Made' if won else 'Lost'
    title = f"{entry['ticker']} {entry['type']} — {entry['date']}: {result_word} ${abs(pnl):.2f}"

    left_str = ''
    if fomo and fomo.get('left_on_table') is not None:
        left_str = f" Left on table: ${fomo['left_on_table']:+.2f}."

    subtitle = (
        f"{entry['ticker']} closed at ${entry['stock_price_at_entry']} on {entry['date']}, "
        f"ranking {entry['signal_rank']} with {entry['signal_pct']:+.2f}% "
        f"(${entry['signal_dollar']:+.2f}). "
        f"Strike ${entry['strike']} {entry['type']} exp {entry['expiration']} "
        f"({entry['dte_at_entry']}DTE). "
        f"IV at entry: {round(entry['iv_at_entry']*100,1)}%. "
        f"Cost: ${entry['cost']:.2f}. "
        f"News scan: {news['ticker_sentiment'] if news else 'n/a'} — "
        f"decision: {news['decision'] if news else 'n/a'}. "
        f"Sold at option value ${exit_['sell_option_price']} (stock open ${exit_['stock_open_price']}) at {exit_['time']}. "
        f"P&L: ${pnl:+.2f}.{left_str}"
    )

    for b in blog:
        if b['trade_id'] == trade['id']:
            b['title']    = title
            b['subtitle'] = subtitle
            b['pnl']      = float(pnl)
            b['won']      = bool(won)
            break

def main():
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    now_pst   = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S PST')
    print(f"sell_signal.py — {now_pst}")

    trades_data  = load_json(TRADES_FILE)
    stats        = load_json(STATS_FILE)
    blog         = load_json(BLOG_FILE)
    excluded_ids = set(trades_data.get('meta', {}).get('excluded_trade_ids', []))

    open_trades = [t for t in trades_data['trades'] if t['status'] == 'open']
    if not open_trades:
        print("No open trades — nothing to sell")
        return

    print(f"Open trades: {[t['entry']['ticker'] for t in open_trades]}")

    for trade in open_trades:
        ticker      = trade['entry']['ticker']
        option_type = trade['entry']['type']
        news        = trade.get('news_scan')
        decision    = news['decision'] if news else 'sell'

        print(f"\n{ticker} {option_type} — decision: {decision.upper()}")

        candles = get_intraday_candles(ticker, today_str)
        if not candles:
            print(f"  No candle data — skipping {ticker}")
            continue

        if decision == 'hold':
            sell_price, sell_time = get_second_candle_price(candles)
            sell_trigger = 'hold_2min'
        else:
            sell_price, sell_time = get_open_price(candles)
            sell_trigger = 'sell_at_open'

        if sell_price is None:
            print(f"  Could not determine sell price — skipping {ticker}")
            continue

        cost = trade['entry']['cost']

        # Gap direction vs thesis
        prior_close = trade['entry']['stock_price_at_entry']
        gap_pct = round((sell_price - prior_close) / prior_close * 100, 2)
        if abs(gap_pct) < 0.1:
            gap_direction = 'flat'
        elif (option_type == 'CALL' and gap_pct > 0) or (option_type == 'PUT' and gap_pct < 0):
            gap_direction = 'with_thesis'
        else:
            gap_direction = 'against_thesis'
        print(f"  Gap: {gap_pct:+.2f}% ({gap_direction})")

        # Stock open price → BS option value
        K         = trade['entry']['strike']
        T_entry   = trade['entry']['T_at_entry']
        sigma     = trade['entry']['iv_at_entry']
        sell_mins = 2 if decision == 'hold' else 1
        T_at_sell = max(T_entry - (sell_mins / (390 * 365)), 0)
        bs_val    = _bs_price(option_type, sell_price, K, T_at_sell, RISK_FREE_RATE, sigma)

        sell_option_price   = round(bs_val, 4)
        sell_contract_value = round(bs_val * 100, 2)
        pnl = round(sell_contract_value - cost, 2)

        print(f"  Sell trigger: {sell_trigger}")
        print(f"  Stock open: ${sell_price} | Option value (BS): ${sell_option_price} | Contract: ${sell_contract_value}")
        print(f"  Cost: ${cost} | P&L: ${pnl:+.2f}")

        fomo = calc_fomo(trade, candles, sell_option_price, sell_time)
        if fomo.get('best_case'):
            print(f"  Best case: ${fomo['best_case']['pnl']:+.2f} | Left on table: ${fomo.get('left_on_table', 0):+.2f}")
            print(f"  {fomo.get('theta_note', '')}")

        trade['status'] = 'closed'
        trade['exit'] = {
            'date':                today_str,
            'time':                sell_time,
            'stock_open_price':    sell_price,
            'sell_option_price':   sell_option_price,
            'sell_contract_value': sell_contract_value,
            'sell_trigger':        sell_trigger,
            'gap_direction':       gap_direction,
            'gap_pct':             gap_pct,
            'pnl':                 pnl
        }
        trade['fomo'] = fomo

        # Raw all-time balance
        trades_data['balance'] = round(trades_data['balance'] + pnl, 2)
        # Clean balance updated inside update_stats
        update_stats(stats, trade, excluded_ids)
        update_blog(blog, trade)

        print(f"  Trade #{trade['id']} closed. Balance: ${trades_data['balance']:+.2f} | Clean: ${stats.get('clean_balance', 0.0):+.2f}")

    # Sync clean_balance back to trades.json
    trades_data['clean_balance'] = stats.get('clean_balance', 0.0)

    save_json(TRADES_FILE, trades_data)
    save_json(STATS_FILE, stats)
    save_json(BLOG_FILE, blog)
    print(f"\nAll done. trades.json, stats.json, blog.json updated.")

if __name__ == '__main__':
    main()
