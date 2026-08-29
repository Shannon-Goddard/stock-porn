# CHANGELOG

All schema changes, bug fixes, and methodology decisions logged here.
Format: `DATE | TYPE | DESCRIPTION`

---

2026-08-28 | bugfix      | sell_signal.py fomo.sell_contract_value was using raw stock price × 100 instead of BS option value. Fixed to use actual sell_option_price × 100.
2026-08-28 | bugfix      | paper_trade.py was allowing 0DTE entries. Added MIN_DTE=1. A 0DTE contract bought at 3:55 PM has ~35 min of market time — not an overnight hold, a lottery ticket with a fuse.
2026-08-28 | bugfix      | paper_trade.py OTM filter: added combined rule — if dte==1 and otm_pct > 20%, skip. Prevents deeply OTM near-expiry contracts that have near-zero probability of value.
2026-08-28 | schema v2.0 | trades.json: added meta block with schema_version, notes, excluded_trade_ids. Trades 1-4 flagged for exclusion from analytics (fomo bug + pre-schema v2.0 fields missing).
2026-08-28 | schema v2.0 | trades.json entry block: added expected_move {one_sigma_pct, upper, lower, strike_position}. Logs the 1σ implied move range at entry time. strike_position: inside/at_edge/outside.
2026-08-28 | schema v2.0 | trades.json exit block: added gap_direction (with_thesis/against_thesis/flat) and gap_pct. Measures whether the stock opened in the direction of our thesis.
2026-08-28 | schema v2.0 | stats.json: added clean_balance field — cumulative P&L excluding trades in meta.excluded_trade_ids. balance field retained as raw all-time number for transparency.
2026-08-28 | schema v2.0 | stats.json: added hypotheses block with 4 active hypotheses to accumulate over 100-trade window: strike_inside_expected_move, gap_with_thesis, macro_keyword_performance, dte_performance.
2026-08-28 | feature     | paper_trade.py: added expected move calculation at entry. Uses IV × sqrt(T) × stock_price to compute 1σ range. Logs upper/lower bounds and strike_position label.
2026-08-28 | feature     | sell_signal.py: added gap_direction and gap_pct to exit block. Compares stock open price to prior close to determine if gap was with or against thesis.
2026-08-28 | feature     | sell_signal.py: update_stats() now respects meta.excluded_trade_ids — excluded trades do not affect clean_balance or hypotheses buckets.
2026-08-28 | feature     | sell_signal.py: update_stats() now updates hypotheses buckets in stats.json (strike_position, gap_direction, dte bucket, macro keywords).
2026-08-28 | feature     | Added pages/findings.html — skeleton page with Active Hypotheses and Findings sections. Reads hypotheses from stats.json. Shows progress toward minimum sample thresholds.
2026-08-28 | feature     | components/nav.js: added Findings link.
2026-08-28 | content     | README.md: added "On Price Prediction" section explaining why price prediction is broken by design and why range prediction is the honest, achievable version.
2026-08-28 | content     | PLAN.md: updated to reflect schema v2.0, new pages, bug fixes, and 5-week findings roadmap.
2026-08-28 | refactor    | scan_options.py replaced entirely. Old script pinged yfinance per ticker (40+ min, timeout risk). New script reads data/cboesymboldirequityindex.csv from CBOE directly — all rows confirmed optionable, no pinging required. Runs in under 1 second.
2026-08-28 | data        | stocks_optionable.csv regenerated from CBOE source. 5,325 symbols (NYSE + Nasdaq + AMEX) vs 1,173 previously passing filters from NYSE-only scan. CRM, CRWD, and all Nasdaq/AMEX optionable stocks now included.
2026-08-28 | cleanup     | Deleted data/scan_progress.csv (old yfinance progress tracker, no longer used). Deleted data/stocks_clean.csv, data/stock ticker-name-sector.csv, data/stock_w_ticker_in_name.csv (NYSE-only source files, replaced by CBOE directory).
2026-08-28 | content     | README.md: updated stack table source, signal filter count, repo structure to reflect CBOE pipeline.
2026-08-28 | content     | pages/data.html: updated stocks_optionable card — description, meta tags, field definition to reflect CBOE source and 5,325 symbol count.
2026-08-28 | content     | PLAN.md: updated stack table, data checklist, key decisions log.
