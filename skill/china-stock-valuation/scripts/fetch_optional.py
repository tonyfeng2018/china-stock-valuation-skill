#!/usr/bin/env python3
"""Optional, non-authoritative market-data connector. Never provides audited statements."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path


def fetch_akshare(ticker):
    try: import akshare as ak
    except ImportError as e: raise RuntimeError('pip install akshare first') from e
    df = ak.stock_zh_a_hist(symbol=ticker,period='daily',start_date=(dt.date.today()-dt.timedelta(days=45)).strftime('%Y%m%d'),end_date=dt.date.today().strftime('%Y%m%d'),adjust='')
    if df is None or df.empty: raise RuntimeError('No market rows returned')
    row=df.iloc[-1].to_dict()
    # Raw vendor keys retained; schema or vendor may change without notice.
    return {'ticker':ticker, 'provider':'AKShare (secondary)', 'market_data':{k:str(v) for k,v in row.items()},
            'retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat(),
            'source_doc':'https://akshare.akfamily.xyz/data/stock/stock.html',
            'warning':'Not independently confirmed. Validate stock identity, trade date and closing price against exchange.'}


def fetch_tushare(ticker):
    try: import tushare as ts
    except ImportError as e: raise RuntimeError('pip install tushare first') from e
    tok=os.getenv('TUSHARE_TOKEN')
    if not tok: raise RuntimeError('TUSHARE_TOKEN not set')
    exchange = 'SH' if ticker.startswith(('6','5')) else 'BJ' if ticker.startswith(('8','4','9')) else 'SZ'
    pro=ts.pro_api(tok)
    df=pro.daily(ts_code=f'{ticker}.{exchange}',start_date=(dt.date.today()-dt.timedelta(days=45)).strftime('%Y%m%d'))
    if df is None or df.empty: raise RuntimeError('No authorized market rows returned')
    row=df.sort_values('trade_date').iloc[-1].to_dict()
    return {'ticker':ticker, 'provider':'Tushare Pro (secondary)','market_data':{k:str(v) for k,v in row.items()},
            'retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat(),
            'source_doc':'https://tushare.pro/document/1?doc_id=27',
            'warning':'Trade data not authorized as primary disclosure; requires exchange validation.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--provider',choices=['akshare','tushare'],required=True)
    p.add_argument('--ticker',required=True,help='6-digit A-share ticker, e.g. 600519')
    p.add_argument('--output',required=True);a=p.parse_args()
    if not (len(a.ticker)==6 and a.ticker.isascii() and a.ticker.isdigit()):raise SystemExit('Expected 6 digits')
    try: data=fetch_akshare(a.ticker) if a.provider=='akshare' else fetch_tushare(a.ticker)
    except Exception as e:raise SystemExit(f'Provider failed: {type(e).__name__}: {str(e)}')
    f=Path(a.output);f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Created {f}; data is UNVERIFIED secondary provider output')
if __name__=='__main__':main()
