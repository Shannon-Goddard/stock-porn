import csv, re

def split_ticker_name(combined):
    # Normal case: find first lowercase letter, step back one for name start
    match = re.search(r'[a-z]', combined)
    if match:
        i = match.start() - 1
        ticker = combined[:i]
        name = combined[i:].rstrip('D')
        return ticker, name

    # All-caps case: ticker is repeated at the start of the name
    # e.g. AMCAMC Networks -> try increasing ticker lengths to find repetition
    combined_stripped = combined.rstrip('D')
    for length in range(1, len(combined_stripped) // 2 + 1):
        ticker = combined_stripped[:length]
        remainder = combined_stripped[length:]
        if remainder.startswith(ticker):
            name = remainder
            return ticker, name

    # Fallback: return whole thing as ticker, empty name
    return combined.rstrip('D'), ''

with open('stock ticker-name-sector.csv', newline='', encoding='utf-8') as infile, \
     open('stocks_clean.csv', 'w', newline='', encoding='utf-8') as outfile:

    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    next(reader)
    writer.writerow(['Symbol', 'Name', 'Sector'])

    for row in reader:
        ticker, name = split_ticker_name(row[0])
        writer.writerow([ticker, name, row[1]])

print("Done!")
