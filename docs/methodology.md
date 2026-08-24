# Methodology
> The secret sauce — published openly because transparency builds trust.
> This is exactly how we generate signals. No black box. No course to sell.

---

## The Core Philosophy

Most retail traders fail because they treat the market as either pure numbers
or pure news. The edge is in combining both — and knowing which one to check first.

```
Macro environment  →  Sector sentiment  →  Individual stock signal
     (water)               (current)              (the fish)

No point analyzing a perfect stock setup
if the macro is about to tank everything.
```

---

## Step 1 — Check the Macro First (SPY/SPX)

Before looking at any individual stock, check whether the market environment
is safe to trade in.

**Why SPY before SPX:**
```
SPY = ETF = retail money moves it = faster reaction = noisier
SPX = index = institutional money = slower but heavier = more meaningful

SPY drops, SPX not confirmed  →  retail panic, possible noise, fade opportunity
SPX confirms the drop         →  institutional selling, respect it, stay out
Same story appearing in both  →  highest weight signal, do not fight it
```

**The diagnostic flow:**
```
Your stock not moving as expected?
→ Check SPY first  (is it the whole market?)
→ Check SPX next   (are institutions confirming?)
→ Both down = market problem, not your stock — thesis may still be intact
→ SPY/SPX fine = something wrong with your thesis — reassess
```

This distinction alone saves more bad trades than any indicator.

---

## Step 2 — Macro Trigger Words

These are headlines on SPY/SPX that move the entire market before
individual stocks react. Scan these first every morning.

| Trigger | Market Reaction | Hidden Opportunity |
|---------|----------------|-------------------|
| Fed / FOMC / Powell | Pause before briefing, direction after | Wait — no trade until after statement |
| CPI / Inflation / PCE | Immediate broad dip | Oversold bounce play 2-3 days later |
| Interest rate hike | Dip — especially tech and growth | REITS, utilities hit hardest |
| Interest rate cut | Run — especially REITS and growth | Rotate into rate-sensitive sectors |
| War / Invasion / Sanctions | Broad market dip | LMT, RTX, NOC, GD, POWW go UP |
| Conflict | Broad market dip | Same defense pairs trade |
| China / Beijing / Tariff / Taiwan | Tanks broad market | Domestic manufacturers go UP (reshoring) |
| Dollar strength / DXY | Emerging markets and commodities dip | Domestic-only companies less affected |

**The pairs trade hiding in every macro trigger:**
Every single macro dip has a sector that benefits from it.
Most retail traders see "China news = sell everything."
The actual trade is "China news = rotate into domestic plays."

**The Thursday Fed pattern:**
FOMC meeting dates are published a year in advance.
The market pauses Wednesday-Thursday before the briefing.
No trade entry during the pause.
After the statement: hawkish language = dip, dovish language = run.
This is free alpha from a calendar lookup — no news scanning needed.

---

## Step 3 — Individual Stock Signals

### Bullish Trigger Words
```
beat expectations        raised guidance
new contract             FDA approval
partnership announced    share buyback
dividend increase        record revenue
expanding into           strategic acquisition
```

### Bearish Trigger Words
```
missed expectations      lowered guidance
investigation            recall
CEO resigned             SEC inquiry
delayed launch           restructuring
layoffs                  debt downgrade
```

### Context Dependent (need surrounding words)
```
acquisition      →  are they buying or being bought?
partnership      →  with who? bigger or smaller company?
restructuring    →  cutting fat (good) or bleeding out (bad)?
beat revenue / missed earnings  →  which matters more for THIS stock?
```

---

## Step 4 — The Signal Scoring System

Not all news sources are equal. We weight them:

```
SEC EDGAR filing              highest weight  (legal, factual)
Earnings call transcript      high weight     (direct from company)
Reuters / Bloomberg           medium-high     (institutional attention)
Yahoo Finance / Google News   medium          (retail attention)
Social sentiment              low weight alone
                              BUT high weight if it CONTRADICTS others
                              — divergence itself is a signal
```

**Scoring:**
```
Score = sum of (source_weight × sentiment_score) across all sources

Score > threshold   →  CALL signal
Score < -threshold  →  PUT signal
Score in middle     →  NO TRADE

The NO TRADE signal is underrated.
Knowing when NOT to trade is half the battle.
```

---

## Step 5 — Smart Money vs Dumb Money

**Unusual options volume:**
Unusual options activity is public data.
If someone buys 10,000 call contracts 3 days before an acquisition announcement
that is visible before the announcement.
High options volume BEFORE a known catalyst = someone knows something.
This is a legitimate signal source and a proxy for insider activity.

**The WSB contrary indicator:**
When retail sentiment (Reddit/social) reaches peak hype on a ticker,
smart money is typically already exiting.
The GME short squeeze worked once because the math was real.
Most of the time peak hype = someone needs you to buy their bags.

```
Smart money (unusual options volume) + technicals agree
AND retail sentiment is on the opposite side
= highest confidence signal
```

**"Buy the rumor, sell the news":**
```
Stock runs UP before the announcement  (rumor phase)
Peaks ON the announcement day
Drops AFTER even if the news is good
Because the people who bought the rumor are now selling to you

Detectable pattern:
Stock up 15%+ in 2 weeks BEFORE earnings
→ post-earnings drop is more likely regardless of actual numbers
```

---

## Step 6 — Price Position (Technical Layer)

```
RSI < 30   →  oversold, potential bounce
RSI > 70   →  overbought, potential pullback
RSI < 40 + price near 52-week low + known catalyst  →  strong CALL setup
RSI > 65 + price near 52-week high + no catalyst    →  strong PUT setup
```

**The key question most retail traders miss:**
Is the bad news already priced in?

A stock down 30% on a bad quarter with a product launch in 60 days
= bad news is priced in, good news is not yet
= the setup most people are too scared to take

---

## Step 7 — Implied Volatility Check

Before buying any option, check the implied volatility (IV).

```
High IV before a known catalyst
→ market is already pricing in a big move
→ options premium is expensive
→ you can be right on direction and still lose money

Low IV + known catalyst approaching
→ cheap premium
→ market hasn't priced in the move yet
→ this is the sweet spot
```

IV crush after earnings is one of the most common ways retail
traders lose money on correct directional calls.
Always check IV before buying premium.

---

## The Trading Timeframe

This system is optimized for **overnight options (next day expiration).**

```
Entry:     End of day — buy into the close
Exit:      Market open — sell into the morning move
Why:       Harvesting the overnight uncertainty premium

Overnight = uncertainty premium built into option price
Open      = uncertainty resolves immediately
            = your profit window
Hold past open = theta accelerates = premium evaporates
```

**The $100/contract filter:**
Keeps every paper trade accessible and risk defined.
Maximum loss = premium paid.
No margin calls. No day trade rules triggered.
Teachable at any account size.

**Pre-market is everything:**
The entire thesis lives in pre-market:
- Futures direction (SPY/SPX overnight)
- Any overnight news on your position
- Earnings releases (always pre-market or after hours)
- Gap up or gap down setting up

---

## Price Reaction Tracking Windows

Different triggers play out on different timescales.
We track each trigger word's historical price reaction at:

```
1 day after trigger
3 days after trigger
7 days after trigger
30 days after trigger
```

Some triggers are priced in immediately.
Some take weeks to play out.
Knowing which is which for a specific stock
is more valuable than any generic signal.

---

## Signal Quality Filters

Before any stock appears in the signal output, it must pass two filters.
These are applied in `fetch_signals.py` at parse time.

```
Minimum price:  $10.00
Minimum volume: 500,000 shares/day (2-day average)
```

**Why $10 price floor:**
Options are priced in $100/contract increments per $1 of underlying move.
A $1 ITM move on a $10 stock = $100 gain — the minimum actionable unit.
Sub-$10 stocks have wide bid/ask spreads, low open interest, and
are frequently untradeable even when options technically exist.
Penny stocks and micro-caps inflate % move lists without being actionable.

Market cap was considered and rejected as a filter.
Market cap penalizes legitimate emerging companies with real momentum.
A $500M cap floor would have excluded early-stage names that later became
the best trades on the list. Price + volume captures liquidity directly
without penalizing growth.

**Why 500,000 daily volume floor:**
Options open interest and bid/ask tightness are downstream of stock volume.
A stock trading 50,000 shares/day will have options with spreads so wide
you lose money on entry. 500K is the practical floor where options
become liquid enough to get a fair fill on a $100/contract trade.

**What these filters do NOT do:**
They do not guarantee options liquidity — always verify open interest
and bid/ask spread in your broker before entering.
They are a first-pass quality gate, not a substitute for due diligence.

---

## The 15-Year Watchlist Principle

No algorithm replaces knowing which stocks are "well behaved" —
meaning they consistently follow these patterns vs ones that are erratic.

A well-behaved stock:
- Reacts predictably to its sector's macro triggers
- Has consistent IV behavior around earnings
- Doesn't gap randomly on low volume
- Has enough options liquidity to get a fair fill

Filtering for well-behaved stocks before applying any signal
is the most underrated edge in retail options trading.

---

## What We Publish That Nobody Else Does

1. The full signal methodology — open source, no black box
2. The trigger word list with historical price reactions
3. Unusual options volume as an insider activity proxy — visible to everyone
4. The NO TRADE signal — when to sit out
5. The pairs trades hidden inside every macro trigger
6. IV check before every paper trade — shown explicitly
7. Running paper trade record — fully transparent wins and losses

---

*This methodology was built from 15 years of watching the market,*
*a $5 to $500 accidental options trade that started it all,*
*and the belief that this information should be free.*

*Not a financial advisor. Built this to earn beer money.*
*All signals are for entertainment and educational purposes only.*
