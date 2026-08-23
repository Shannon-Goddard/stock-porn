import csv

check = {'ACMA', 'ADSE', 'CRH', 'CTW', 'FIG', 'FTRK', 'RH', 'MED', 'MPLX', 'MWA', 'NGL', 'NNOX', 'JBS', 'IVR', 'LOBO', 'SPPL', 'STRT', 'VTEX'}

with open('stocks_clean.csv', newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if row[0] in check:
            print(row)
