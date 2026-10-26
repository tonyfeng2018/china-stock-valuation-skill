#!/usr/bin/env python3
"""Compare two dated normalized research snapshots. Does not fetch any news or market data."""
import argparse
import json
from pathlib import Path

# These are *suggested* configurable defaults, not proven universal thresholds.
RULES = {
  ('financials','revenue_growth_yoy_pct'):(8.0,'percentage-points','营收同比增速'),
  ('financials','adjusted_profit_growth_yoy_pct'):(10.0,'percentage-points','扣非归母利润同比增速'),
  ('financials','gross_margin_pct'):(3.0,'percentage-points','毛利率'),
  ('financials','net_debt_100m'):(15.0,'RMB 100m','净债务'),
  ('company','close_price_rmb'):(0.08,'relative','收盘价'),
  ('analysis','fair_value_base_rmb'):(0.15,'relative','基准公允价'),
}

def get_path(d, path):
    for key in path:
        if not isinstance(d,dict): return None
        d=d.get(key)
    return d


def compare(old, new, rules=RULES):
    out=[]
    for path,(th,metric,label) in rules.items():
        o=get_path(old,path);n=get_path(new,path)
        if not isinstance(o,(int,float)) or isinstance(o,bool) or not isinstance(n,(int,float)) or isinstance(n,bool): continue
        if metric=='relative':
            if o==0: continue
            delta=(n/o-1)*100
            significant=abs(delta)>=th*100
            display='相对变化百分比'
        else:
            delta=n-o
            significant=abs(delta)>=th
            display='百分点' if metric=='percentage-points' else '亿元'
        if significant:
            out.append({'kind':'market' if path[0]=='company' else 'valuation' if path[0]=='analysis' else 'fundamental',
                        'metric':'.'.join(path),'label':label,'old':o,'new':n,'delta':round(delta,3), 'delta_unit':display,
                        'alert':'需人工核验','reason':'越过默认阈值，不代表已确认基本面重大变化'})
    old_ids={str(x.get('id')) for x in old.get('events',[]) if isinstance(x,dict) and x.get('id')}
    for e in new.get('events',[]):
        if isinstance(e,dict) and e.get('id') and str(e['id']) not in old_ids:
            out.append({'kind':e.get('kind','event'),'label':e.get('title','新增事件'), 'event_id':e['id'],
                        'source_url':e.get('source_url'),'status':e.get('status','未核实'),
                        'alert':'新事件待评估', 'reason':'新增事件需要判断影响链条和正式生效状态'})
    return {'old_as_of':old.get('as_of'), 'new_as_of':new.get('as_of'), 'ticker':get_path(new,('company','ticker')),
            'warning':'Simple threshold detector only; metrics must have equivalent accounting periods and definitions.',
            'alerts':out, 'count':len(out)}


def main():
    p=argparse.ArgumentParser(description='Compare two existing snapshots')
    p.add_argument('--old',required=True);p.add_argument('--new',required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    old=json.loads(Path(a.old).read_text(encoding='utf-8'));new=json.loads(Path(a.new).read_text(encoding='utf-8'))
    if get_path(old,('company','ticker')) != get_path(new,('company','ticker')): raise SystemExit('Ticker mismatch')
    result=compare(old,new)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Created {path} with {result["count"]} alerts')
if __name__=='__main__':main()
