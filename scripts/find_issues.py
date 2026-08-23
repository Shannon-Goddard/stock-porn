import csv, re

with open('stock ticker-name-sector.csv', newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        combined = row[0]
        match = re.search(r'[a-z]', combined)
        if not match:
            print('NO_LOWER:', repr(combined))
        else:
            i = match.start() - 1
            ticker = combined[:i]
            name = combined[i:].rstrip('D')
            # flag where name starts with all caps word (like AMC Networks)
            if re.match(r'^[A-Z]{2,}[\s,]', name):
                print(repr(ticker), '|', repr(name))
