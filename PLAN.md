# stock-porn.loyal9.app — Project Plan
> "Because numbers are sexy and fun to watch"
> Living document — updated as we build

---

## The Mission
Democratize what hedge funds charge for.
Give retail traders the same tools, data, and methodology for free.
Set up as a joke. Deliver real alpha. Cover our ass legally.

---

## The Stack (All Free)
| Layer | Tool |
|-------|------|
| Data source | Yahoo Finance (yfinance) |
| News/Charts | Think or Swim (user side) |
| Execution | Robinhood (user side) |
| Stock list | Our cleaned NYSE CSV (GitHub) |
| Live data | GitHub Actions (scheduled Python) |
| Hosting | GitHub Pages |
| User sheet | Google Sheets + GOOGLEFINANCE() |
| Domain | stock-porn.loyal9.app |
| Math | Black-Scholes (scipy) |

---

## The Data
- [x] Raw CSV cleaned — ticker/name/sector separated
- [x] All-caps edge cases fixed
- [x] options_available scan script built (scan_options.py)
- [x] stocks_optionable.csv — 2863 optionable stocks
- [x] metadata.json — auto timestamped, filter counts per stage
- [x] signals.json — top 10% movers, top 5 dollar movers
- [x] Quality filters added: MIN_PRICE=$10, MIN_AVG_VOLUME=500K
- [x] Filter counts tracked in metadata (no_data, bad_values, zero_change, below_min_price, below_min_volume, passed)
- [ ] trades.json — paper trade ledger (Phase 3)
- [ ] stats.json — derived analytics (Phase 3)
- [ ] blog.json — auto-generated article entries (Phase 4)
- [ ] data/candles/ — intraday 1-min candles per open contract (Phase 3)
- [ ] watchlist.csv — curated tickers (future)

---

## Signal Quality Filters
Documented in docs/methodology.md — Signal Quality Filters section.

```
MIN_PRICE = $10.00
  → ATM options on sub-$10 stocks exceed $100 budget
  → Bid/ask spreads untradeable
  → Market cap rejected as alternative — penalizes emerging companies

MIN_AVG_VOLUME = 500,000 shares/day
  → Options open interest is downstream of stock volume
  → Below 500K = wide spreads, can't get fair fill on $100 contract

EXPIRATION FILTER = 7 days max (Phase 3)
  → Quarterly contracts: ATM premium exceeds $100 budget
  → Theta burn makes overnight hold inefficient
  → yfinance 1-min candle history only available for 7 days
  → All four reasons point the same direction
```

---

## Signal System — Layers

### Layer 1: Macro Environment (check first, always)
SPY/SPX based — is the water safe to swim in?

| Trigger | Reaction | Notes |
|---------|----------|-------|
| Fed/FOMC week | Pause — wait for briefing | Thursday pattern |
| Inflation (CPI/PCE) | Market dips | Bounce play opportunity |
| Interest rate hike | Dip — especially tech/growth | |
| Interest rate cut | Run — especially REITS/utilities | |
| War/Conflict | Broad dip | PAIRS: LMT, RTX, NOC, GD, POWW go UP |
| China news | Tanks broad market | PAIRS: domestic manufacturers go UP |
| Dollar strength (DXY) | Emerging markets/commodities dip | |

**SPY vs SPX diagnostic:**
```
SPY drops, SPX not confirmed = retail panic = possible noise = fade opportunity
SPX confirms = institutional selling = respect it
Same story in both = highest weight signal
```

**Top % gainer at close = elevated PUT candidate overnight:**
```
Big Friday runner → profit taking overnight → gap down at open
This is not a coincidence — it is a repeatable, documentable setup
Your signal may be accidentally correct for the right reason
Direction of signal matters as much as magnitude
```

### Layer 2: Individual Stock Signals

**Bullish triggers:**
beat expectations, raised guidance, new contract, FDA approval,
partnership announced, share buyback, dividend increase, record revenue,
expanding into, strategic acquisition

**Bearish triggers:**
missed expectations, lowered guidance, investigation, recall,
CEO resigned, SEC inquiry, delayed launch, restructuring,
layoffs, debt downgrade

**Context dependent (need surrounding words):**
acquisition, partnership, restructuring, beat revenue / missed earnings

### Layer 3: Smart Money vs Dumb Money
```
Unusual options volume BEFORE catalyst = someone knows something
WSB peak hype = smart money already exiting
"Buy the rumor, sell the news" = detectable pre-announcement run pattern
```

**Scoring system:**
```
SEC filing          = highest weight
Earnings transcript = high weight
Reuters/Bloomberg   = medium-high
Yahoo/Google News   = medium
Social sentiment    = low UNLESS contradicts others (divergence = signal)

Score > threshold   = CALL
Score < -threshold  = PUT
Score in middle     = NO TRADE
```

---

## The Trading Methodology
> Full detail in docs/methodology.md

**Timeframe:** Overnight options, 7-day max expiration
**Entry:** 3:55 PM PST — automated, no human input
**News scan:** 6:25 AM PST — Yahoo Finance, held tickers + SPY + SPX
**Exit:** 6:31 AM PST — automated
- Bearish keywords confirm PUT thesis → hold 2 min → sell at 6:32 AM
- No confirmation → sell at open (6:30 AM first clean candle)
- 2-minute hold is a hard stop — THETA on 0DTE is violent past that

**The $100/contract rule:**
- ATM strike, closest to ITM within $100 budget
- Consistent across all trades — no exceptions
- Makes every trade comparable in the ledger

**Contract selection — two contracts per night:**
```
Contract 1: top dollar gainer → CALL (overnight fade candidate)
Contract 2: top dollar loser  → PUT  (overnight bounce candidate)
SPY hedge: added only when macro triggers are active (not automatic)
```

**Why both contracts:**
- Safety net against overnight news swinging opposite direction
- One leg almost always wins
- Max exposure $200/night, both legs defined risk

---

## Paper Trade System (Phase 3)

### Automated Flow
```
3:55 PM PST  paper_trade.py
  → reads signals.json
  → selects ATM contracts within $100 budget (7-day exp only)
  → captures IV from options chain
  → logs entry to trades.json
  → auto-generates note from signal data + macro context
  → generates blog.json entry skeleton

6:25 AM PST  fetch_news.py
  → scans Yahoo Finance news for held tickers + SPY + SPX
  → handles weekend gap (last scan date → current date)
  → scores keywords: bullish / bearish / neutral
  → logs decision to trades.json
  → fetches + stores 1-min candles to data/candles/{ticker}_{date}.json

6:31 AM PST  sell_signal.py
  → reads decision from trades.json
  → fetches first clean 1-min candle (6:30 AM open price)
  → hold decision → uses second candle (6:32 AM)
  → logs sell price + time
  → runs Black-Scholes FOMO calculation
  → updates stats.json
  → updates blog.json entry with trade data
```

### Black-Scholes FOMO Calculator (scripts/black_scholes.py)
```
Inputs captured at entry:
  S  = stock price at entry       (from signals.json)
  K  = strike price               (from options chain at close)
  T  = DTE / 365                  (1/365 for 0DTE, up to 7/365)
  r  = 0.05 (hardcoded risk-free) (close enough, consistent)
  σ  = IV at entry                (from options chain at close)

FOMO calculated at:
  → intraday high (stock price + time)
  → intraday low  (stock price + time)
  → theoretical option value at each extreme
  → max gain and max loss in dollars
  → theta burn estimate by 10 AM vs open value

DTE-aware theta note:
  0DTE: "Theta burned $X in first 30 min — 0DTE decay is violent"
  1DTE: "Theta moderate at open, accelerating by noon"
  4DTE: "Theta minimal at open, stock direction dominates"

Phase 1: Black-Scholes estimates (labeled as theoretical)
Phase 2: Compare against real contract prices when available
         → accuracy of BS model becomes its own research dataset
```

### trades.json Structure
```json
{
  "balance": 100.00,
  "first_trade_date": "YYYY-MM-DD",
  "trades": [{
    "id": 1,
    "status": "open|closed",
    "entry": {
      "date", "time", "ticker", "type (PUT/CALL)",
      "strike", "expiration", "dte_at_entry",
      "stock_price_at_entry", "premium", "cost",
      "iv_at_entry", "signal_rank", "signal_pct",
      "signal_dollar", "sector", "spy_change",
      "macro_active", "auto_note"
    },
    "news_scan": {
      "scanned_at", "gap_days", "ticker_sentiment",
      "spy_sentiment", "keywords_found",
      "decision (hold|sell)", "decision_reason"
    },
    "exit": {
      "date", "time", "sell_price", "pnl",
      "sell_trigger (open|hold_2min)"
    },
    "fomo": {
      "day_high": { "stock_price", "time", "bs_option_value", "theoretical_pnl" },
      "day_low":  { "stock_price", "time", "bs_option_value", "theoretical_pnl" },
      "theta_note"
    }
  }]
}
```

---

## Analytics (Phase 3 — stats.json)
All derived from trades.json. Updated after every trade closes.

```
Overall:          total trades, win rate, avg P&L, current balance
By day of week:   win rate Mon-Fri (proves/disproves theta efficiency thesis)
By sector:        which sectors overnight fade most reliably
By signal rank:   does dollar_loser_1 outperform dollar_loser_2?
SPY correlation:  PUT win rate on SPY up days vs SPY down days
FOMO:             avg left on table, hold_2min vs sell_at_open avg P&L
IV crush:         avg IV at entry vs back-calculated IV at open
Keyword accuracy: bullish/bearish/neutral fired vs correct
Methodology score: each of 7 layers scored independently for prediction accuracy
```

**Research value hiding in this data:**
- Theta efficiency by DTE (Thursday vs Monday entry)
- Black-Scholes accuracy vs real contract prices (Phase 2 comparison)
- IV crush in real dollars — nobody publishes this with actual trade data
- Keyword predictive accuracy — turns opinion into evidence over time

---

## Site Structure

### Pages
```
index.html                  → signals grid only, nav, one-line disclaimer
pages/paper-trade.html      → current hold + yesterday's result + last 5 trades
pages/ledger.html           → full trade history, checkbook style, all-time P&L
pages/stats.html            → analytics dashboard, all derived metrics
pages/blog.html             → auto-generated articles, YouTube embeds
pages/methodology.html      → rendered methodology content
pages/legal.html            → full disclaimer, not-a-financial-advisor, LLC notice
```

### Navigation — components/nav.js
```
Single file. Every page adds:
  <div id="nav-root"></div>
  <script src="../components/nav.js"></script>
Update nav.js = all pages updated simultaneously.

Nav items:
  Home | Paper Trade | Ledger | Stats | Blog | Methodology
  ────────────────────────────────────────────────────────
  GitHub (external) | Legal | Buy Dev a Beer (external)
```

### Blog — components/blog-engine.js
```
Auto-generated from trades.json + blog.json
Article skeleton fills itself from trade data:
  Title:    "{TICKER} {PUT/CALL} — {DATE}: How We Made/Lost ${PNL}"
  Subtitle: auto-filled from signal_rank, keywords, decision, P&L, FOMO
  Sections: Signal → News Scan → Trade → FOMO → Greeks → What We Learned
  YouTube:  embed placeholder, you add ID when video is ready
  Images:   placeholder, you drop screenshots in when ready
published: true by default — article live immediately, enrich later
```

---

## GitHub Repo Structure
```
/
├── README.md
├── PLAN.md (this file)
├── requirements.txt
├── index.html
├── /components
│   ├── nav.js              ← hamburger nav, one file rules all pages
│   └── blog-engine.js      ← renders blog articles from trade data
├── /pages
│   ├── paper-trade.html
│   ├── ledger.html
│   ├── stats.html
│   ├── blog.html
│   ├── methodology.html
│   └── legal.html
├── /data
│   ├── stocks_clean.csv ✓
│   ├── stocks_optionable.csv ✓
│   ├── metadata.json ✓
│   ├── signals.json ✓
│   ├── trades.json
│   ├── stats.json
│   ├── blog.json
│   └── candles/            ← {ticker}_{date}.json per open contract
├── /scripts
│   ├── split_tickers.py ✓
│   ├── scan_options.py ✓
│   ├── fetch_signals.py ✓
│   ├── black_scholes.py
│   ├── fetch_news.py
│   ├── paper_trade.py
│   └── sell_signal.py
├── /docs
│   ├── methodology.md ✓
│   └── google-sheets-guide.md ✓
└── /.github/workflows
    ├── update_signals.yml ✓
    ├── monthly_rescan.yml ✓
    ├── paper_trade_entry.yml   ← 3:55 PM PST (23:55 UTC) weekdays
    ├── paper_trade_news.yml    ← 6:25 AM PST (14:25 UTC) weekdays
    └── paper_trade_sell.yml    ← 6:31 AM PST (14:31 UTC) weekdays
```

---

## To-Do List

### Phase 1 — Foundation ✓ Complete
- [x] GitHub repo
- [x] stocks_clean.csv
- [x] scan_options.py
- [x] fetch_signals.py
- [x] update_signals.yml
- [x] monthly_rescan.yml
- [x] index.html — live at stock-porn.loyal9.app
- [x] metadata.json with filter counts
- [x] requirements.txt
- [x] Quality filters: MIN_PRICE=$10, MIN_AVG_VOLUME=500K
- [x] Filter decision documented in methodology.md
- [x] Push filtered signals

### Phase 2 — Navigation & Legal ✓ Complete
- [x] components/nav.js — hamburger, all pages
- [x] pages/legal.html
- [x] pages/methodology.html
- [x] index.html — nav added, footer cleaned

### Phase 3 — Paper Trade System
- [x] data/trades.json — initialized (balance = cumulative P&L from $0)
- [x] data/stats.json — initialized
- [x] data/candles/ — folder created
- [x] scripts/black_scholes.py — verified $698.69 on HOOD example
- [x] scripts/fetch_news.py — Yahoo news, keyword scoring, candle fetch, weekend gap handling
- [x] scripts/paper_trade.py — entry automation, real options chain, ATM within $100, otm_pct tracked
- [x] scripts/sell_signal.py — BS option pricing at open, FOMO calc, stats + blog update
- [x] .github/workflows/paper_trade_entry.yml — 3:55 PM PST, DST covered
- [x] .github/workflows/paper_trade_news.yml — 6:25 AM PST, DST covered
- [x] .github/workflows/paper_trade_sell.yml — 6:31 AM PST, DST covered
- [x] requirements.txt — scipy added
- [ ] pages/paper-trade.html
- [ ] pages/ledger.html

### Phase 4 — Analytics & Blog
- [ ] data/stats.json populated by sell_signal.py
- [ ] data/blog.json auto-generated by sell_signal.py
- [ ] components/blog-engine.js
- [ ] pages/stats.html
- [ ] pages/blog.html
- [ ] YouTube video — Google Sheets setup (link when recorded)

### Phase 5 — README.md
- [ ] Write after everything else is built
- [ ] Origin story ($5 to $500 moment)
- [ ] Full methodology summary
- [ ] Contributing guidelines (community trigger words)

---

## Open Questions
- [ ] Unusual options volume — best free source?
- [ ] WSB sentiment — Reddit API still viable?
- [ ] Phase 2: real contract prices for BS model accuracy comparison
- [ ] Logo/branding — later

---

## Key Decisions Log
| Decision | Reason | Date |
|----------|--------|------|
| MIN_PRICE=$10 | Sub-$10 options untradeable, spreads too wide | Jan 2025 |
| MIN_AVG_VOLUME=500K | Options OI downstream of stock volume | Jan 2025 |
| Market cap filter rejected | Penalizes emerging companies | Jan 2025 |
| 7-day expiration max | Budget, theta, yfinance 1-min data limit | Jan 2025 |
| Black-Scholes only | Teachable, no noise from other Greeks models | Jan 2025 |
| Two contracts/night | Safety net, one leg almost always wins | Jan 2025 |
| SPY hedge not automatic | Only on active macro triggers per methodology | Jan 2025 |
| Fully automated entry/exit | No human bias, fully transparent | Jan 2025 |
| sell_at_open default | IV crush + theta make holding past open costly | Jan 2025 |
| hold_2min on bullish news | First 2 min most volatile, max theta burn after | Jan 2025 |

---

## Contributions Found So Far
1. SPY/SPX divergence as a signal (retail vs institutional confirmation)
2. Pairs trades hidden inside macro triggers
3. IV check before buying premium
4. Overnight uncertainty premium harvesting
5. NO TRADE as a signal
6. Source weighting scoring system
7. Price reaction windows (1/3/7/30 days)
8. "Buy the rumor sell the news" as detectable pattern
9. Unusual options volume as insider activity proxy
10. WSB contrary indicator
11. Top % gainer at close = elevated PUT candidate (overnight fade pattern)
12. Theta efficiency by DTE — Thursday entry outperforms Monday (hypothesis)
13. IV crush measurement in real dollars — publishable research
14. Keyword accuracy rate — turns trigger word list from opinion into evidence
15. Black-Scholes estimate vs real contract price comparison (Phase 2)

---

*Last updated: Phase 3 scripts + workflows complete — pages next*
*Next step: paper-trade.html → ledger.html → stats.html → blog.html*
