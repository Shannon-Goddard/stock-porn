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

---

## The Data
- [x] Raw CSV cleaned — ticker/name/sector separated
- [x] All-caps edge cases fixed
- [x] options_available scan script built (scan_options.py)
- [x] stocks_optionable.csv — generating now (~4940 stocks)
- [x] metadata.json — auto timestamped on every scan/update
- [ ] Add watchlist column (curated by us)
- [x] Published to GitHub repo

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

### Layer 2: Individual Stock Signals

**Bullish triggers:**
- beat expectations
- raised guidance
- new contract
- FDA approval
- partnership announced
- share buyback
- dividend increase
- record revenue
- expanding into
- strategic acquisition

**Bearish triggers:**
- missed expectations
- lowered guidance
- investigation
- recall
- CEO resigned
- SEC inquiry
- delayed launch
- restructuring
- layoffs
- debt downgrade

**Context dependent (need surrounding words):**
- acquisition (buying or being bought?)
- partnership (with who?)
- restructuring (cutting fat or bleeding out?)
- beat revenue / missed earnings (which matters more for THIS stock?)

### Layer 3: Smart Money vs Dumb Money
```
Unusual options volume BEFORE catalyst = someone knows something
WSB peak hype on a ticker = smart money already exiting
Inverse WSB signal = legitimate contrary indicator
"Buy the rumor, sell the news" = stock runs PRE-announcement, 
                                  drops ON announcement
                                  even if news is good
```

**Scoring system:**
```
Score = (source_weight × sentiment_score) summed
SEC filing          = highest weight
Earnings transcript = high weight
Reuters/Bloomberg   = medium-high weight
Yahoo/Google News   = medium weight
Social sentiment    = low weight UNLESS it contradicts others
                      (divergence itself is a signal)

Score > threshold   = CALL signal
Score < -threshold  = PUT signal
Score in middle     = NO TRADE (knowing when NOT to trade matters)
```

---

## The Trading Methodology
> This is the secret sauce — published openly in the README

**Timeframe:** Overnight options (next day expiration)
**Entry:** End of day scan → buy into close
**Exit:** Market open → sell into the morning move
**Why:** Harvesting overnight uncertainty premium
         Open resolves uncertainty = profit window
         Hold past open = theta accelerates = bad

**The $100/contract filter:**
- Keeps it accessible
- Defined maximum loss
- No margin calls
- Teachable at any account size

**Pre-trade checklist (runs automatically):**
```
1. Is it a Fed week? → reduce or skip
2. SPY trend last 5 days → bullish/bearish/neutral
3. SPX confirms or diverges?
4. Any macro triggers in last 48hrs?
5. Individual stock catalyst present?
6. Implied volatility check → is premium cheap or expensive?
7. IF all green → signal fires
   IF macro hostile → no trade regardless of stock setup
```

**Price reaction tracking windows:**
```
1 day after trigger
3 days after trigger
7 days after trigger
30 days after trigger
```
Different triggers play out on different timescales.

---

## The Page — index.html

### Header
"Because numbers are sexy and fun to watch"

### Disclaimer
Humorous but legally covers the LLC.
"Not a financial advisor... I did this to earn beer."
- Link: buymeacoffee labeled "Buy the dev a beer" / "Beer Money"

### Main Display
```
Full NYSE list
→ filtered: options_available = TRUE
→ Top 10% gainers / Top 10% losers
→ Drill down: Top 5 dollar gainers / Top 5 dollar losers
```

### Paper Trade Section (Phase 2)
```
Daily at ~3:30 PM EST:
- System shows the setup
- Shows the trade with reasoning visible
- Shows cost (filtered to ~$100 contracts)
- Call or Put with methodology explained
- Next morning: result revealed
- Running track record — fully transparent
```

### Methodology Section
- Signal layers explained in plain English
- Trigger word list visible
- SPY/SPX diagnostic explained
- "Buy the rumor sell the news" explained
- Insider activity (unusual options volume) tracker

---

## GitHub Repo Structure
```
/
├── README.md (last — documents what we built)
├── PLAN.md (this file)
├── REQUIREMENTS.txt
├── index.html ✓ live at stock-porn.loyal9.app
├── /data
│   ├── stocks_clean.csv ✓
│   ├── stocks_optionable.csv ✓ (generating)
│   ├── metadata.json ✓ (auto timestamped)
│   ├── signals.json (generated by GitHub Action)
│   └── watchlist.csv (curated — todo)
├── /scripts
│   ├── split_tickers.py ✓
│   ├── scan_options.py ✓
│   ├── fetch_signals.py ✓
│   ├── macro_scan.py (Phase 2)
│   └── paper_trade.py (Phase 3)
├── /docs
│   ├── methodology.md ✓
│   └── google-sheets-guide.md ✓
└── .github/workflows
    ├── update_signals.yml ✓ (every 30 min market hours)
    └── monthly_rescan.yml ✓ (1st of every month)
```

---

## To-Do List

### Phase 1 — Foundation
- [x] Set up GitHub repo
- [x] Add stocks_clean.csv
- [x] Build scan_options.py — generates options_available column
- [x] Build fetch_signals.py — yfinance batch data pull
- [x] Set up update_signals.yml — GitHub Action every 30 min market hours
- [x] Set up monthly_rescan.yml — GitHub Action 1st of every month
- [x] Build index.html — live at stock-porn.loyal9.app
- [x] Disclaimer copy
- [x] BuyMeACoffee integration
- [x] metadata.json — auto timestamp on every update
- [x] requirements.txt
- [ ] Build trigger word list (user to contribute from experience)
- [x] BuyMeACoffee actual account link — buymeacoffee.com/goddardshannon9
- [ ] Add watchlist.csv (curated)

### Phase 2 — Signal System
- [ ] Sentiment scoring system
- [ ] SPY/SPX diagnostic layer
- [ ] Unusual options volume tracker
- [ ] WSB contrary indicator
- [ ] Implied volatility check
- [ ] Pre-trade checklist automation

### Phase 3 — Paper Trade
- [ ] Daily signal display
- [ ] Next day result reveal
- [ ] Running track record
- [ ] Methodology explanation per trade

### Phase 4 — Google Sheets Template
- [x] GOOGLEFINANCE() setup guide — docs/google-sheets-guide.md
- [x] Step by step directions
- [ ] YouTube video link (add when recorded)
- [ ] Screenshots/examples

### Phase 5 — README.md
- [ ] Write after everything else is built
- [ ] Origin story ($5 to $500 moment)
- [ ] Full methodology documented
- [ ] How to use the sheet
- [ ] How to use TOS alongside this tool
- [ ] Contributing guidelines (community trigger words)

---

## Open Questions
- [ ] How often can we hit yfinance for free before getting rate limited?
- [ ] Best free source for options chain data (for paper trade)?
- [ ] Logo scraping from TradingView URLs — later
- [ ] Unusual options volume — best free source?
- [ ] WSB sentiment scraping — Reddit API still viable?

---

## Contributions Found So Far
Things discovered during planning that weren't in original concept:
1. SPY/SPX divergence as a signal (retail vs institutional confirmation)
2. Pairs trades hidden inside macro triggers (war = defense stocks up)
3. Implied volatility check before buying premium
4. Overnight uncertainty premium harvesting (why open > hold)
5. NO TRADE as a signal (knowing when to sit out)
6. Source weighting vs majority rules voting
7. Price reaction windows (1/3/7/30 days) per trigger
8. "Buy the rumor sell the news" as a detectable pattern
9. Unusual options volume as insider activity proxy
10. WSB contrary indicator

---
*Last updated: scan running — 2150/4940 stocks processed*
*Next step: finish scan → test fetch_signals.py → wire metadata timestamp to index.html*
