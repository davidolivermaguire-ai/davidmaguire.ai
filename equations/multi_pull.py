# multi_pull.py - pull daily adjusted closes for a basket of Nasdaq-100 names + the index.
# Run in PowerShell:  py "C:\Users\david\OneDrive\Desktop\Archive\Trading Strategies\davidmaguire-ai\equations\multi_pull.py"
# One-time setup:     pip install yfinance pandas

import sys
from pathlib import Path
import yfinance as yf                       # Yahoo Finance downloader

TICKERS = ["^NDX", "AAPL", "MSFT", "NVDA", "PEP"]   # index + four Nasdaq-100 constituents
START   = "2015-01-01"                       # plenty of history; we slice the window later
OUT     = Path(__file__).with_name("multi_daily.csv")   # save the CSV beside this script

# auto_adjust=True -> split/dividend-adjusted closes, the CORRECT basis for equity returns
# (NVDA/AAPL/MSFT have splits and dividends; the ^NDX price index is unaffected either way).
close = yf.download(TICKERS, start=START, auto_adjust=True, progress=False)["Close"]

close = close.reindex(columns=TICKERS)       # stable column order; a failed ticker -> NaN column
close.columns = ["NDX" if c == "^NDX" else c for c in close.columns]   # tidy the index name

if close.dropna(how="all").empty:            # guard: nothing came back at all
    sys.exit("Download failed - check your connection or the tickers.")

close = close.dropna(how="any")              # keep only dates where EVERY series has a price (aligned panel)
close.to_csv(OUT)                            # Date index + one column per ticker

print(f"Saved {len(close)} rows x {close.shape[1]} tickers to {OUT}")
print(close.tail(3).to_string())             # sanity check: the three most recent rows
