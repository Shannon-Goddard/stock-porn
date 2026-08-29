# stock-porn.loyal9.app
> "Because numbers are sexy and fun to watch"

Democratize what hedge funds charge for. Give retail traders the same tools, data, and methodology for free. Set up as a joke. Deliver real alpha. Cover our ass legally.

Live at **[stock-porn.loyal9.app](https://stock-porn.loyal9.app)**

---

## Origin Story

It started with a $5 options contract on a stock I barely understood.

I bought it on a gut feeling — a headline I half-read, a chart that looked "right," and the kind of confidence that only comes from not knowing what you don't know. It hit. $5 turned into $500 overnight.

That trade was dumb luck. But it asked a real question: *what would it look like if you did that systematically?*

Fifteen years of watching the market later, I had a methodology in my head that I'd never written down. Signal layers. Macro filters. Trigger words. IV checks. The pairs trades hiding inside every macro event. The NO TRADE signal that saves more money than any entry ever will.

None of it was secret. All of it was learnable. None of it was free anywhere.

So I built this.

---

## What This Is

A fully automated paper trading system that:

- Scans 5,300+ optionable US stocks daily via GitHub Actions (NYSE, Nasdaq, AMEX)
- Filters to liquid, tradeable signals (price ≥ $10, volume ≥ 500K/day)
- Selects two overnight options contracts at 3:55 PM PST — one CALL, one PUT
- Scans pre-market news at 6:25 AM PST and scores bullish/bearish keywords
- Exits at 6:31 AM PST with Black-Scholes FOMO calculations on every trade
- Publishes every trade, every decision, every win and loss — fully transparent

No black box. No course to sell. No Discord with a monthly fee.

---

## The Methodology

Seven layers, checked in order. Full detail in [docs/methodology.md](docs/methodology.md).

**Layer 1 — Macro environment (check first, always)**
SPY vs SPX divergence tells you whether you're watching retail panic or institutional selling. They're not the same thing and they don't call for the same response.

**Layer 2 — Macro trigger words**
Fed/FOMC, CPI, rate decisions, war, China news — each one has a predictable market reaction and a pairs trade hiding inside it that most retail traders miss entirely.

**Layer 3 — Individual stock signals**
Bullish and bearish trigger words weighted by source. SEC filing outweighs a Reddit post. Earnings transcript outweighs Yahoo Finance. The scoring system turns opinion into a number.

**Layer 4 — Smart money vs dumb money**
Unusual options volume before a catalyst is public data. When retail sentiment peaks, smart money is usually already exiting. These two signals together — especially when they contradict each other — are the highest-confidence setups.

**Layer 5 — "Buy the rumor, sell the news"**
A stock up 15%+ in the two weeks before earnings is more likely to drop after the announcement regardless of the actual numbers. Detectable. Repeatable. Documentable.

**Layer 6 — Price position**
RSI + 52-week range + known catalyst. The question most retail traders never ask: is the bad news already priced in?

**Layer 7 — IV check before buying premium**
You can be right on direction and still lose money if IV is already elevated. Always check before buying. IV crush after earnings is one of the most common ways correct directional calls turn into losses.

---

## On Price Prediction (And Why We Don't Do It)

Everyone wants a stock price predictor. We get it.

Here's why that's not what this is — and why what we're building is actually more useful:

**Price prediction is broken by design.**
The moment a prediction is widely known, it changes the behavior it's predicting. A perfect predictor would destroy itself. Beyond that: earnings surprises are genuinely unknowable, fund liquidations are invisible until after the fact, and black swans don't exist in historical data until they do.

**Range prediction is different — and it's already in the math.**
Implied Volatility isn't our opinion. It's the options market's collective bet on how far a stock could move. The 1σ expected move — calculated directly from IV and time to expiration — is right roughly 68% of the time by definition. That's not a claim. That's statistics.

What we're building toward:
- Not *where* the stock goes — but *how far* it could go
- Not a price target — but a range that tells you whether a contract is worth buying before you pick a direction
- Not a prediction — a probability-weighted filter that gets better with every trade logged

**The "prints harder" principle.**
A 30% OTM contract on a stock that gaps 35% returns more than a 5% OTM contract on a 5% mover. The math is the same. The difference is knowing the expected move range before you enter — so you're not buying a 30% OTM contract on a stock that historically moves 4%. That's not a bet. That's a donation.

We have 4 trades. We need 100. Check back in 5 weeks.

---

## The Trade Structure

**Two contracts per night:**
- Contract 1: top dollar gainer → CALL (overnight fade candidate)
- Contract 2: top dollar loser → PUT (overnight bounce candidate)

**The $100/contract rule:**
ATM strike, closest to ITM within a $100 budget. Consistent across every trade. Makes every entry comparable in the ledger. Maximum loss = premium paid. No margin calls.

**Entry:** 3:55 PM PST — automated, no human input
**News scan:** 6:25 AM PST — Yahoo Finance, held tickers + SPY + SPX
**Exit:** 6:31 AM PST — automated
- Bearish keywords confirm PUT thesis → hold 2 min → sell at 6:32 AM
- No confirmation → sell at open (6:30 AM first clean candle)
- 2-minute hold is a hard stop — theta on 0DTE is violent past that

---

## Signal Quality Filters

```
MIN_PRICE = $10.00
  → ATM options on sub-$10 stocks exceed $100 budget
  → Bid/ask spreads untradeable at that price range

MIN_AVG_VOLUME = 500,000 shares/day
  → Options open interest is downstream of stock volume
  → Below 500K = wide spreads, can't get a fair fill on a $100 contract

EXPIRATION = 7 days max
  → Quarterly contracts: ATM premium exceeds $100 budget
  → Theta burn makes overnight hold inefficient
  → yfinance 1-min candle history only available for 7 days
```

Of 5,325 optionable stocks sourced from the CBOE symbol directory: **the daily pass count varies** based on price and volume filters.

---

## The Stack

| Layer | Tool |
|-------|------|
| Data source | Yahoo Finance (yfinance) |
| Options math | Black-Scholes (scipy) |
| Automation | GitHub Actions |
| Hosting | GitHub Pages |
| User sheet | Google Sheets + GOOGLEFINANCE() |
| Domain | stock-porn.loyal9.app |
| Options universe | CBOE symbol directory (NYSE + Nasdaq + AMEX) |

Everything is free. No API keys required to run the site. No paid data feeds.

---

## Research Value

This project generates data nobody else publishes with actual trade records attached:

- **Theta efficiency by DTE** — does Thursday entry outperform Monday? The data will answer this.
- **IV crush in real dollars** — not theoretical. Actual premium paid vs actual open price.
- **Black-Scholes accuracy vs real contract prices** — the model's error rate becomes its own dataset.
- **Keyword predictive accuracy** — the trigger word list starts as opinion. Over time it becomes evidence.
- **SPY/SPX divergence as a signal** — retail vs institutional confirmation, tracked per trade.

---

## Site

| Page | What's There |
|------|-------------|
| [Home](https://stock-porn.loyal9.app) | Live signals grid, top movers |
| [Paper Trade](https://stock-porn.loyal9.app/pages/paper-trade.html) | Current hold + yesterday's result + last 5 trades |
| [Ledger](https://stock-porn.loyal9.app/pages/ledger.html) | Full trade history, all-time P&L |
| [Stats](https://stock-porn.loyal9.app/pages/stats.html) | Analytics dashboard, all derived metrics |
| [Blog](https://stock-porn.loyal9.app/pages/blog.html) | Auto-generated trade articles |
| [Methodology](https://stock-porn.loyal9.app/pages/methodology.html) | Full signal methodology |
| [Sheets Guide](https://stock-porn.loyal9.app/pages/sheets-guide.html) | Build your own live tracking sheet in Google Sheets |
| [Findings](https://stock-porn.loyal9.app/pages/findings.html) | Active hypotheses + findings after 100 trades |
| [Data](https://stock-porn.loyal9.app/pages/data.html) | Download all data files, API access |
| [Legal](https://stock-porn.loyal9.app/pages/legal.html) | Full disclaimer |

---

## Repo Structure

```
/
├── index.html                  ← signals grid
├── /components
│   ├── nav.js                  ← one file controls all page navigation
│   └── blog-engine.js          ← renders trade articles from blog.json
├── /pages                      ← all site pages
├── /data
│   ├── cboesymboldirequityindex.csv ← CBOE full US options symbol directory
│   ├── metadata.json           ← filter counts, last updated timestamp
│   ├── signals.json            ← top movers, updated daily
│   ├── trades.json             ← full paper trade ledger
│   ├── stats.json              ← derived analytics
│   ├── blog.json               ← auto-generated article data
│   └── candles/                ← 1-min intraday candles per open contract
├── /scripts
│   ├── fetch_signals.py        ← daily signal generation
│   ├── scan_options.py         ← monthly optionable stock scan
│   ├── paper_trade.py          ← 3:55 PM entry automation
│   ├── fetch_news.py           ← 6:25 AM news scan + keyword scoring
│   ├── sell_signal.py          ← 6:31 AM exit + Black-Scholes FOMO calc
│   └── black_scholes.py        ← options pricing model
├── /docs
│   ├── methodology.md          ← full signal methodology
│   └── google-sheets-guide.md  ← sheets setup walkthrough
└── /.github/workflows          ← automated daily/monthly schedules
```

---

## Contributing

The trigger word lists in `fetch_news.py` are the most improvable part of this system.

If you know a keyword that reliably moves a stock or sector and isn't in the list, open a PR. The format is simple — bullish words, bearish words, context-dependent words with notes on what surrounding context changes the signal.

The goal is to turn the trigger word list from opinion into evidence over time. Every trade that fires on a keyword gets logged. Accuracy rates accumulate. Bad keywords get cut. Good ones get weighted higher.

That's the contribution loop.

---

## Legal

Not a financial advisor. This is a paper trading system for educational and entertainment purposes. No real money is traded. Past paper trade performance does not predict future real-money results.

Full disclaimer at [stock-porn.loyal9.app/pages/legal.html](https://stock-porn.loyal9.app/pages/legal.html)

---

## Credits

Built by [@goddardshannon9](https://buymeacoffee.com/goddardshannon9) and [Amazon Q](https://aws.amazon.com/q/developer/) — AWS's AI coding assistant, which co-authored every script, page, and workflow in this repo from scratch.

The methodology is 15 years of market watching. The implementation is what happens when you describe that methodology out loud to an AI that can actually build it.

---

*Not a financial advisor. Built this to earn beer money.*
*[🍺 Buy the dev a beer](https://buymeacoffee.com/goddardshannon9)*
