import yfinance as yf
import csv
import time
import os
import json
from datetime import datetime, timezone

INPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'stocks_clean.csv')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'stocks_optionable.csv')
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'scan_progress.csv')

def load_stocks():
    stocks = []
    with open(INPUT_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stocks.append(row)
    return stocks

def load_progress():
    """Resume from where we left off if scan was interrupted"""
    completed = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                completed[row['Symbol']] = row['options_available']
    return completed

def has_options(ticker):
    try:
        t = yf.Ticker(ticker)
        dates = t.options
        return len(dates) > 0
    except Exception:
        return False

def main():
    stocks = load_stocks()
    completed = load_progress()

    total = len(stocks)
    remaining = [s for s in stocks if s['Symbol'] not in completed]

    print(f"Total stocks: {total}")
    print(f"Already scanned: {len(completed)}")
    print(f"Remaining: {len(remaining)}")
    print("Starting scan... (this will take a while)")
    print("Safe to interrupt — progress is saved and will resume\n")

    # Open progress file in append mode
    progress_mode = 'a' if os.path.exists(PROGRESS_FILE) else 'w'
    progress_f = open(PROGRESS_FILE, progress_mode, newline='', encoding='utf-8')
    progress_writer = csv.writer(progress_f)
    if progress_mode == 'w':
        progress_writer.writerow(['Symbol', 'options_available'])

    count = len(completed)
    for stock in remaining:
        symbol = stock['Symbol']
        result = has_options(symbol)
        completed[symbol] = 'TRUE' if result else 'FALSE'
        progress_writer.writerow([symbol, 'TRUE' if result else 'FALSE'])
        progress_f.flush()

        count += 1
        status = '✓ options' if result else '✗ no options'
        print(f"[{count}/{total}] {symbol:<10} {status}")

        # Be polite to Yahoo Finance — don't hammer it
        time.sleep(0.5)

    progress_f.close()

    # Write final output CSV with options_available column
    print("\nWriting final output...")
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Symbol', 'Name', 'Sector', 'options_available'])
        for stock in stocks:
            symbol = stock['Symbol']
            opt = completed.get(symbol, 'FALSE')
            writer.writerow([symbol, stock['Name'], stock['Sector'], opt])

    optionable = sum(1 for v in completed.values() if v == 'TRUE')

    # Write metadata.json with timestamp and stats
    metadata_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'metadata.json')
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        metadata = {}

    metadata['stocks_optionable'] = {
        'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        'total_stocks': total,
        'optionable': optionable,
        'non_optionable': total - optionable
    }

    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nDone!")
    print(f"Optionable stocks: {optionable}")
    print(f"Non-optionable:    {total - optionable}")
    print(f"Output saved to:   data/stocks_optionable.csv")
    print(f"Timestamp saved to: data/metadata.json")

if __name__ == '__main__':
    main()
