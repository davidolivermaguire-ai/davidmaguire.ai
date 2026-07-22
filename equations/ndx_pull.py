# ndx_pull.py - pull Nasdaq-100 (^NDX) daily history and save to CSV
# Run in PowerShell:  py ndx_pull.py     (or)   python ndx_pull.py
# One-time setup:     pip install yfinance pandas

import sys
from pathlib import Path
import yfinance as yf                     # Yahoo Finance downloader

TICKER = "^NDX"                           # Nasdaq-100 PRICE index (not QQQ, not ^IXIC)
START  = "2015-01-01"                     # pull plenty of history; we slice the window later
OUT    = Path(__file__).with_name("ndx_daily.csv")   # save the CSV beside this script

# auto_adjust=False keeps the raw index 'Close'. An index has no dividends/splits,
# so adjusted == close here, but being explicit avoids version-dependent surprises.
df = yf.download(TICKER, start=START, auto_adjust=False, progress=False)

if df.empty:                             # guard: a failed download returns an empty frame
    sys.exit("Download failed - check your connection or the ^NDX ticker.")

# Recent yfinance versions return MultiIndex columns like ('Close','^NDX'); flatten them.
if getattr(df.columns, "nlevels", 1) > 1:
    df.columns = df.columns.get_level_values(0)

df = df.reset_index()                    # turn the DatetimeIndex into a normal 'Date' column
df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]   # tidy, predictable column order
df.to_csv(OUT, index=False)              # write CSV with Date as YYYY-MM-DD

print(f"Saved {len(df)} rows to {OUT}")
print(df.tail(3).to_string(index=False))  # sanity check: show the three most recent rows
