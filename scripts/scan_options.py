import csv
import json
import os
import re
from datetime import datetime, timezone

CBOE_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'cboesymboldirequityindex.csv')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'stocks_optionable.csv')
METADATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'metadata.json')

# Skip symbols that yfinance/options chains can't handle cleanly
SYMBOL_PATTERN = re.compile(r'^[A-Z]{1,5}$')

def main():
    stocks = []
    with open(CBOE_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row[' Stock Symbol'].strip()
            name = row['Company Name'].strip().strip('"')
            if not SYMBOL_PATTERN.match(symbol):
                continue
            stocks.append({'Symbol': symbol, 'Name': name})

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Symbol', 'Name', 'Sector', 'options_available'])
        for s in stocks:
            writer.writerow([s['Symbol'], s['Name'], 'Unknown', 'TRUE'])

    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        metadata = {}

    metadata['stocks_optionable'] = {
        'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        'source': 'CBOE symbol directory',
        'total_stocks': len(stocks),
        'optionable': len(stocks),
        'non_optionable': 0
    }

    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f"Done. {len(stocks)} optionable symbols written to data/stocks_optionable.csv")

if __name__ == '__main__':
    main()
