# settle

Compare two money ledgers and say whether they balance. Match is on `id`. Amounts are cents.

```
python3 -m settle fixtures/payments.csv fixtures/deposits.csv
```

```
MATCHED 2  150.00
MISMATCH inv-3  payments.csv 40.00  deposits.csv 40.50
ONLY payments.csv  inv-9  12.00
ONLY deposits.csv  inv-8  5.00
BALANCE no
```

Each CSV header is `id,amount`. An id may appear once in a file. `MATCHED` counts ids whose amounts are equal, and the figure next to it is the sum of those amounts. A mismatch stays out of that sum. `BALANCE yes` means every id is on both sides and every amount agrees. The same two files always print the same text.

## Will not do

- Fuzzy names, date windows, or splitting one payment across many ids
- Bank-specific formats
- Uploads or a stored balance
- Treating a duplicate id as two payments

## Tests

```
python3 -m unittest discover -s tests -v
```

Python 3.11 or newer. The standard library is enough.

## License

MIT.
