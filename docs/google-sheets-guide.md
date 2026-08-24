# Build Your Own Live Stock Sheet with Google Sheets
> No coding required. Free. Updates automatically.
> Takes about 10 minutes to set up.

---

## What You'll Build

A personal live stock tracking sheet that:
- Pulls real-time price data automatically
- Shows price, change %, change $, volume
- Highlights gainers green and losers red
- Filters to only stocks with options available
- Is yours to customize however you want

---

## Step 1 — Get the Data

1. Go to the [stock-porn GitHub repo](https://github.com/Shannon-Goddard/stock-porn)
2. Navigate to `data/stocks_optionable.csv`
3. Click the **Download raw file** button
4. Save it to your computer

This CSV contains every NYSE listed stock with options available,
including ticker symbol, company name, and sector.

---

## Step 2 — Open Google Sheets

1. Go to [sheets.google.com](https://sheets.google.com)
2. Click the **+** to create a new blank spreadsheet
3. Name it something like `My Stock Sheet`

---

## Step 3 — Import the CSV

1. Click **File** → **Import**
2. Click **Upload** → select the `stocks_optionable.csv` you downloaded
3. Import location: **Replace current sheet**
4. Separator type: **Comma**
5. Click **Import data**

You should now see columns:
```
A: Symbol  |  B: Name  |  C: Sector  |  D: options_available
```

---

## Step 4 — Add Live Price Columns

Click on cell **E1** and add these headers across the top row:

| E1 | F1 | G1 | H1 | I1 |
|----|----|----|----|----|
| Price | Change $ | Change % | Volume | 52W High |

Now in **E2** enter this formula:
```
=IFERROR(GOOGLEFINANCE(A2,"price"),"—")
```

In **F2** enter:
```
=IFERROR(GOOGLEFINANCE(A2,"changepct")/100,"—")
```

In **G2** enter:
```
=IFERROR(GOOGLEFINANCE(A2,"change"),"—")
```

In **H2** enter:
```
=IFERROR(GOOGLEFINANCE(A2,"volume"),"—")
```

In **I2** enter:
```
=IFERROR(GOOGLEFINANCE(A2,"high52"),"—")
```

---

## Step 5 — Apply Formulas to All Rows

1. Select cells **E2:I2**
2. Copy them (Ctrl+C)
3. Select from **E3** all the way down to the last row of your data
4. Paste (Ctrl+V)

All rows will now pull live data automatically.

> **Note:** Google Sheets has a limit of 1000 GOOGLEFINANCE calls per sheet.
> If you have more rows than that, split into multiple sheets or
> filter down to your watchlist first.

---

## Step 6 — Format the Sheet

**Format Change % as percentage:**
1. Select column F
2. Click **Format** → **Number** → **Percent**

**Format Price and Change $ as currency:**
1. Select columns E and G
2. Click **Format** → **Number** → **Currency**

**Freeze the header row:**
1. Click **View** → **Freeze** → **1 row**

---

## Step 7 — Add Color (the fun part)

Make gainers green and losers red automatically:

1. Select column G (Change %)
2. Click **Format** → **Conditional formatting**
3. Add rule: **Greater than** `0` → fill color **green**
4. Add another rule: **Less than** `0` → fill color **red**

Repeat for column F (Change $) if you want both colored.

---

## Step 8 — Filter to Your Watchlist (Optional)

To track only specific stocks:

1. Click **Data** → **Create a filter**
2. Click the filter arrow on column A (Symbol)
3. Search for and select only the tickers you want to watch

Or create a second sheet tab called `Watchlist` and manually
enter just your tickers in column A, then use the same
GOOGLEFINANCE formulas in columns B onward.

---

## Useful GOOGLEFINANCE Formulas Reference

| Formula | What it returns |
|---------|----------------|
| `=GOOGLEFINANCE(A2,"price")` | Current price |
| `=GOOGLEFINANCE(A2,"change")` | Dollar change today |
| `=GOOGLEFINANCE(A2,"changepct")` | Percent change today |
| `=GOOGLEFINANCE(A2,"volume")` | Today's volume |
| `=GOOGLEFINANCE(A2,"high52")` | 52-week high |
| `=GOOGLEFINANCE(A2,"low52")` | 52-week low |
| `=GOOGLEFINANCE(A2,"pe")` | Price to earnings ratio |
| `=GOOGLEFINANCE(A2,"marketcap")` | Market cap |
| `=GOOGLEFINANCE(A2,"shares")` | Shares outstanding |

---

## Pro Tips

**Check if a stock is near its 52-week high:**
```
=IFERROR(E2/GOOGLEFINANCE(A2,"high52"),"—")
```
A value close to 1.0 means the stock is near its 52-week high.
A value close to 0.5 means it's trading near the middle of its range.

**Calculate RSI manually? Don't.**
Use the price history formula instead to spot trends:
```
=GOOGLEFINANCE(A2,"close",TODAY()-30,TODAY())
```
This pulls 30 days of closing prices into a mini table.
Paste it into a separate area and chart it.

**Sort by biggest movers:**
1. Click **Data** → **Sort range**
2. Sort by column G (Change %) descending
3. Biggest gainers float to the top

---

## Keeping Your Data Fresh

The `stocks_optionable.csv` on GitHub is refreshed monthly.
Check back on the first of each month and re-download if you want
the most current list of optionable stocks.

The GOOGLEFINANCE prices update automatically — no action needed.

---

## Want More?

- 📊 See the live example at [stock-porn.loyal9.app](https://stock-porn.loyal9.app)
- 📖 Read the [full methodology](methodology.md) behind the signals
- ⭐ Star the [GitHub repo](https://github.com/Shannon-Goddard/stock-porn) to get notified of updates
- 🍺 [Buy the dev a beer](https://buymeacoffee.com) if this saved you money

---

*Not a financial advisor. Built this to earn beer money.*
*All data is for entertainment and educational purposes only.*
