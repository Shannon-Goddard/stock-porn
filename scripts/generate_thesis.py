import json
import re
from datetime import datetime, timedelta, timezone
from collections import Counter
import yfinance as yf

THESIS_PATH = "data/thesis.json"
TRADES_PATH = "data/trades.json"
RESOLVE_WEEKS = 8
TOP_PICKS = 3

ETF_SECTORS = {
    "SPY":  "Broad Market",
    "QQQ":  "Broad Market",
    "IWM":  "Broad Market",
    "DIA":  "Broad Market",
    "XLK":  "Tech",
    "QTUM": "Tech",
    "ARKK": "Tech",
    "BOTZ": "Tech",
    "XLY":  "Consumer Discretionary",
    "XLP":  "Consumer Staples",
    "XRT":  "Retail",
    "XLF":  "Financials",
    "KRE":  "Regional Banks",
    "HYG":  "Credit",
    "XLE":  "Energy",
    "USO":  "Energy",
    "UNG":  "Energy",
    "PDBC": "Commodities",
    "IYT":  "Transportation",
    "XLV":  "Healthcare",
    "XBI":  "Biotech",
    "ITA":  "Defense",
    "VNQ":  "Real Estate",
    "XLU":  "Utilities",
    "BITO": "Crypto",
    "VXX":  "Volatility",
    "GLD":  "Safe Haven",
    "SLV":  "Safe Haven",
}

# Hardcoded sector stock maps — liquid, optionable names per sector
SECTOR_STOCKS = {
    "Broad Market":            ["AAPL", "MSFT", "AMZN", "GOOGL", "META"],
    "Tech":                    ["NVDA", "AMD", "AVGO", "TSM", "QCOM", "IONQ", "RGTI", "IBM"],
    "Consumer Discretionary":  ["TSLA", "AMZN", "HD", "MCD", "NKE", "BKNG"],
    "Consumer Staples":        ["WMT", "PG", "KO", "PEP", "COST", "MDLZ"],
    "Retail":                  ["WMT", "TGT", "COST", "AMZN", "TJX", "ROST"],
    "Financials":              ["JPM", "BAC", "GS", "MS", "WFC", "BLK"],
    "Regional Banks":          ["USB", "PNC", "TFC", "CFG", "FITB", "HBAN"],
    "Credit":                  ["JPM", "BAC", "AXP", "COF", "SYF", "DFS"],
    "Energy":                  ["XOM", "CVX", "COP", "SLB", "EOG", "PXD", "EQT", "AR", "CTRA", "RRC"],
    "Transportation":          ["UPS", "FDX", "DAL", "UAL", "CSX", "UNP"],
    "Healthcare":              ["UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK"],
    "Biotech":                 ["MRNA", "BNTX", "REGN", "VRTX", "GILD", "BIIB"],
    "Defense":                 ["LMT", "RTX", "NOC", "GD", "BA", "HII"],
    "Real Estate":             ["AMT", "PLD", "EQIX", "SPG", "O", "WELL"],
    "Utilities":               ["NEE", "DUK", "SO", "D", "AEP", "EXC"],
    "Crypto":                  ["COIN", "MSTR", "MARA", "RIOT", "CLSK", "HUT"],
    "Volatility":              ["UVXY", "SVXY", "VIXY"],
    "Safe Haven":              ["GLD", "SLV", "NEM", "AEM", "WPM", "GOLD"],
    "Commodities":             ["FCX", "NEM", "AA", "CLF", "MP", "VALE"],
}

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "as", "is", "it", "its", "by", "from", "that", "this",
    "are", "was", "were", "be", "been", "has", "have", "had", "not", "no",
    "up", "down", "after", "before", "over", "under", "into", "out", "about",
    "than", "more", "less", "will", "would", "could", "should", "may", "can",
    "s", "re", "t", "he", "she", "they", "we", "i", "you", "his", "her",
    "their", "our", "what", "which", "who", "how", "when", "where", "why",
    "stock", "stocks", "market", "markets", "share", "shares", "price",
    "trading", "trade", "trades", "investor", "investors", "etf", "fund",
    "today", "week", "month", "year", "day", "new", "says", "said",
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def now_pst():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def resolve_by_date():
    return (datetime.now(timezone.utc) + timedelta(weeks=RESOLVE_WEEKS)).strftime("%Y-%m-%d")


# --- keyword aggregation from raw_headlines ---

def get_weekly_keywords(trades):
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    words = []
    for t in trades:
        ns = t.get("news_scan")
        if not ns or not ns.get("raw_headlines"):
            continue
        scanned_at = ns.get("scanned_at", "")
        try:
            scan_dt = datetime.strptime(scanned_at[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if scan_dt < cutoff:
            continue
        for bucket in ["ticker", "spy", "spx"]:
            for headline in ns["raw_headlines"].get(bucket, []):
                tokens = re.findall(r"[a-z]+", headline.lower())
                words.extend([w for w in tokens if w not in STOPWORDS and len(w) > 3])
    return Counter(words)


# --- ETF relative strength ---

def get_etf_signals(etfs):
    signals = {}
    tickers = yf.download(etfs, period="14d", interval="1d", progress=False, auto_adjust=True)["Close"]
    for etf in etfs:
        try:
            prices = tickers[etf].dropna()
            if len(prices) < 6:
                continue
            week_return = (prices.iloc[-1] - prices.iloc[-6]) / prices.iloc[-6] * 100
            two_week_return = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0] * 100
            signals[etf] = {
                "week_return": round(float(week_return), 2),
                "two_week_return": round(float(two_week_return), 2),
                "price": round(float(prices.iloc[-1]), 2),
            }
        except Exception:
            continue
    return signals


# --- options flow anomaly ---

def get_options_flow(etfs):
    flow = {}
    for etf in etfs:
        try:
            tk = yf.Ticker(etf)
            exps = tk.options
            if not exps:
                continue
            opt = tk.option_chain(exps[0])
            calls = opt.calls
            avg_vol = calls["volume"].mean()
            max_vol = calls["volume"].max()
            if avg_vol > 0:
                flow[etf] = round(float(max_vol / avg_vol), 2)
        except Exception:
            continue
    return flow


# --- score each ETF ---

def score_etfs(etf_signals, flow, keywords):
    scores = {}
    for etf, sig in etf_signals.items():
        score = 0
        score += sig["week_return"] * 2
        score += sig["two_week_return"]
        if etf in flow:
            score += min(flow[etf], 5) * 3
        sector = ETF_SECTORS.get(etf, "")
        sector_words = [w.lower() for w in sector.split()]
        for word in sector_words:
            score += keywords.get(word, 0) * 0.5
        scores[etf] = round(score, 2)
    return scores


# --- pick top 3 stocks within winning sector ---

def get_top_picks(sector, etf_signals):
    # Use hardcoded map first, fall back to ETF-only if sector not mapped
    candidates_tickers = SECTOR_STOCKS.get(sector, [])

    # If UNG is the signal ETF, bias toward nat gas names
    if not candidates_tickers:
        sector_etfs = [e for e, s in ETF_SECTORS.items() if s == sector and e in etf_signals]
        candidates_tickers = sector_etfs

    candidates = []
    for sym in candidates_tickers:
        try:
            h = yf.Ticker(sym).history(period="7d")
            if h.empty or len(h) < 2:
                continue
            wr = (h["Close"].iloc[-1] - h["Close"].iloc[0]) / h["Close"].iloc[0] * 100
            av = h["Volume"].mean()
            price = float(h["Close"].iloc[-1])
            candidates.append({
                "ticker": sym,
                "week_return": round(float(wr), 2),
                "avg_volume": int(av),
                "price": round(price, 2),
            })
        except Exception:
            continue

    candidates.sort(key=lambda x: abs(x["week_return"]), reverse=True)
    seen = set()
    unique = []
    for c in candidates:
        if c["ticker"] not in seen:
            seen.add(c["ticker"])
            unique.append(c)
    return unique[:TOP_PICKS]


# --- build thesis text ---

def build_thesis_text(winning_etf, sector, week_return, two_week_return, flow_ratio, top_keywords, picks, direction):
    kw_str = ", ".join(f"'{k}'" for k, _ in top_keywords[:5]) if top_keywords else "none detected"
    flow_str = f"Options flow anomaly on {winning_etf}: {flow_ratio}x avg call volume. " if flow_ratio and flow_ratio > 1.5 else ""
    pick_str = ", ".join(f"{p['ticker']} ({p['week_return']:+.1f}% wk)" for p in picks)
    return (
        f"Sector rotation signal: {sector}. "
        f"{winning_etf} {week_return:+.2f}% (1wk) / {two_week_return:+.2f}% (2wk) vs SPY. "
        f"{flow_str}"
        f"Top keywords this week: {kw_str}. "
        f"Direction: {direction}. "
        f"Top picks: {pick_str}."
    )


# --- resolve open theses ---

def resolve_open(theses):
    today = now_pst()
    for thesis in theses:
        if thesis["status"] != "open":
            continue
        if thesis["resolve_by"] > today:
            continue
        confirmed = 0
        for pick in thesis["picks"]:
            try:
                tk = yf.Ticker(pick["ticker"])
                hist = tk.history(period="5d")
                if hist.empty:
                    continue
                current_price = round(float(hist["Close"].iloc[-1]), 2)
                pick["price_at_resolution"] = current_price
                pct = (current_price - pick["price_at_prediction"]) / pick["price_at_prediction"] * 100
                pick["pct_change"] = round(pct, 2)
                moved_correctly = (
                    (thesis["direction"] == "bullish" and pct > 0) or
                    (thesis["direction"] == "bearish" and pct < 0)
                )
                if moved_correctly:
                    confirmed += 1
            except Exception:
                continue

        if confirmed == TOP_PICKS:
            outcome = "confirmed"
        elif confirmed >= 2:
            outcome = "partial"
        else:
            outcome = "refuted"

        thesis["status"] = "closed"
        thesis["resolution"] = {
            "date": today,
            "outcome": outcome,
            "confirmed_picks": confirmed,
            "notes": f"{confirmed}/{TOP_PICKS} picks moved in predicted direction.",
            "rolled_into": None,
        }
    return theses


# --- link related theses ---

def link_theses(theses, new_thesis):
    linked = []
    for t in theses:
        if t["id"] == new_thesis["id"]:
            continue
        if t["sector"] == new_thesis["sector"]:
            linked.append(t["id"])
            continue
        existing_kw = set(t.get("top_keywords", []))
        new_kw = set(new_thesis.get("top_keywords", []))
        if len(existing_kw & new_kw) >= 2:
            linked.append(t["id"])
    return linked


# --- main ---

def main():
    data = load_json(THESIS_PATH)
    trades_data = load_json(TRADES_PATH)
    trades = trades_data.get("trades", [])
    etfs = data["meta"]["etf_basket"]

    # resolve any expired open theses first
    data["theses"] = resolve_open(data["theses"])

    # gather signals
    keywords = get_weekly_keywords(trades)
    etf_signals = get_etf_signals(etfs)
    flow = get_options_flow(etfs)

    if not etf_signals:
        print("No ETF signal data available — market may be closed.")
        save_json(THESIS_PATH, data)
        return

    # get SPY baseline
    spy_week = etf_signals.get("SPY", {}).get("week_return", 0)

    # score relative to SPY
    scores = score_etfs(etf_signals, flow, keywords)
    if not scores:
        print("No scores generated.")
        save_json(THESIS_PATH, data)
        return

    winning_etf = max(scores, key=scores.get)
    losing_etf = min(scores, key=scores.get)

    # pick direction based on whether winner is outperforming or underperforming
    winner_return = etf_signals[winning_etf]["week_return"]
    direction = "bullish" if winner_return > spy_week else "bearish"
    signal_etf = winning_etf if direction == "bullish" else losing_etf
    sector = ETF_SECTORS.get(signal_etf, "Unknown")

    top_keywords = [(w, c) for w, c in keywords.most_common(20) if len(w) > 4]
    picks_raw = get_top_picks(sector, etf_signals)

    picks = []
    for p in picks_raw:
        picks.append({
            "ticker": p["ticker"],
            "direction": direction,
            "price_at_prediction": p["price"],
            "price_at_resolution": None,
            "pct_change": None,
        })

    sig = etf_signals.get(signal_etf, {})
    flow_ratio = flow.get(signal_etf)
    thesis_text = build_thesis_text(
        signal_etf,
        sector,
        sig.get("week_return", 0),
        sig.get("two_week_return", 0),
        flow_ratio,
        top_keywords,
        picks_raw,
        direction,
    )

    new_id = max((t["id"] for t in data["theses"]), default=0) + 1
    new_thesis = {
        "id": new_id,
        "written_date": now_pst(),
        "resolve_by": resolve_by_date(),
        "sector": sector,
        "signal_etf": signal_etf,
        "direction": direction,
        "thesis": thesis_text,
        "evidence": {
            "etf_week_return": sig.get("week_return"),
            "etf_two_week_return": sig.get("two_week_return"),
            "options_flow_ratio": flow_ratio,
            "top_keywords": [w for w, _ in top_keywords[:10]],
            "spy_week_return": spy_week,
        },
        "top_keywords": [w for w, _ in top_keywords[:10]],
        "picks": picks,
        "status": "open",
        "resolution": None,
        "linked_thesis_ids": [],
    }

    new_thesis["linked_thesis_ids"] = link_theses(data["theses"], new_thesis)
    data["theses"].append(new_thesis)

    save_json(THESIS_PATH, data)
    print(f"Thesis #{new_id} written: {sector} ({direction}) — resolve by {new_thesis['resolve_by']}")


if __name__ == "__main__":
    main()
