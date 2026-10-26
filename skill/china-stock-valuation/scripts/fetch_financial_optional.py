#!/usr/bin/env python3
"""Fetch raw three statements via optional vendors (NOT official source verification).
Provider fields, values and schemas remain unnormalized on purpose; official
filings must be verified before any valuation.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path


def market_prefix(ticker):
    if ticker.startswith(('6','5')): return 'SH'
    if ticker.startswith(('0','3','2')): return 'SZ'
    if ticker.startswith(('4','8','9')): return 'BJ'
    raise ValueError('Unsupported/ambiguous A-share code; verify exchange manually')


def clean(rows):
    # pandas handles NaN / Timestamps; converting to string preserves raw fields
    # without claiming accounting normalization.
    return [{str(k): (None if v is None or str(v) in ('nan','NaT') else str(v)) for k,v in r.items()} for r in rows]


def from_akshare(ticker):
    import akshare as ak
    sym=market_prefix(ticker)+ticker
    out={}
    methods={'income':ak.stock_profit_sheet_by_report_em,
             'balance_sheet':ak.stock_balance_sheet_by_report_em,
             'cash_flow':ak.stock_cash_flow_sheet_by_report_em}
    for key, fn in methods.items():
        try:
            df=fn(symbol=sym)
            out[key]={'rows':clean(df.to_dict('records')),'row_count':len(df),'status':'ok'}
        except Exception as e:
            out[key]={'status':'error','error':type(e).__name__+': '+str(e)[:300]}
    return out, 'AKShare via upstream Eastern Fortune (secondary; availability/schema may change)'


def from_tushare(ticker, start):
    import tushare as ts
    token=os.environ.get('TUSHARE_TOKEN')
    if not token:raise RuntimeError('TUSHARE_TOKEN missing')
    pro=ts.pro_api(token)
    sym=ticker+'.'+market_prefix(ticker)
    out={}
    for key, method in [('income',pro.income),('balance_sheet',pro.balancesheet),('cash_flow',pro.cashflow),('indicator',pro.fina_indicator)]:
        try:
            df=method(ts_code=sym,start_date=start)
            out[key]={'rows':clean(df.to_dict('records')),'row_count':len(df),'status':'ok'}
        except Exception as e:
            out[key]={'status':'error','error':type(e).__name__+': '+str(e)[:300]}
    return out, 'Tushare Pro (secondary; financial APIs require appropriate access/points)'


def main():
    p=argparse.ArgumentParser();p.add_argument('--provider',required=True,choices=['akshare','tushare'])
    p.add_argument('--ticker',required=True,help='6-digit A-share symbol')
    p.add_argument('--start',default='20230101',help='Tushare announcement-date start YYYYMMDD')
    p.add_argument('--output',required=True);a=p.parse_args()
    if not (a.ticker.isascii() and a.ticker.isdigit() and len(a.ticker)==6):raise SystemExit('Expected six-digit ticker')
    try: sheets,provider=from_akshare(a.ticker) if a.provider=='akshare' else from_tushare(a.ticker,a.start)
    except ImportError as e:raise SystemExit('Install optional dependency: pip install '+a.provider) from e
    except Exception as e:raise SystemExit(f'Provider unavailable: {e}')
    payload={'ticker':a.ticker,'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
             'provider':provider,'status':'raw_unverified','unit':'ORIGINAL PROVIDER UNIT (NOT RMB 100m)',
             'source_docs':'https://akshare.akfamily.xyz/data/stock/stock.html' if a.provider=='akshare' else 'https://tushare.pro/document/1?doc_id=108',
             'warnings':['This is not an official disclosure audit.','Reporting period vs announcement date requires reconciliation.',
                         'Do not pass raw values directly to run_analysis.py before normalization, unit checks and official filing validation.'],
             'tables':sheets}
    f=Path(a.output);f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Created raw unverified financial statement extracts:',f)
    for k,v in sheets.items():print(k,v['status'],v.get('row_count',v.get('error','')))
if __name__=='__main__':main()
