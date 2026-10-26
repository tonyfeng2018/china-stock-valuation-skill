#!/usr/bin/env python3
"""Offline illustrative A-share valuation/research dashboard from verified JSON input.
No real market fetch, no automatic source verification, no investment recommendation.
Python >=3.10, standard library only.
"""
import argparse
import datetime as dt
import html
import json
import math
from pathlib import Path


def num(x, name):
    if x is None:
        return None
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f"{name}: expected finite number")
    return float(x)


def valuation(s):
    """Compute three assumption-driven scenarios with multiple model cross-checks.

    Units: market value and accounting amounts are RMB 100m, shares in 100m shares,
    prices in RMB/share. Scenario-specific operating inputs optionally override
    base historic normalization. Does not verify any financial source.
    """
    c=s['company']; f=s['financials']; a=s.get('assumptions',{})
    shares=num(c.get('shares_100m'),'shares_100m')
    price=num(c.get('close_price_rmb'),'close_price_rmb')
    if shares is None or shares <= 0 or price is None or price <= 0:
        raise ValueError('Need positive shares_100m and close_price_rmb')
    market_cap=price*shares
    business_type=s.get('business_type','nonfinancial')
    financial_sector=business_type in ('bank','insurance','broker')
    warnings=[]
    forecasts=a.get('scenario_forecasts',{})
    weights=a.get('weights', {'pe':0.3,'pb':0.1,'dcf':0.3,'ev_ebitda':0.2,'sotp':0.1})
    allowed={'pe','pb','dcf','ev_ebitda','sotp'}
    if not weights or any(k not in allowed for k in weights):
        raise ValueError('weights must use supported model keys only')
    weights={k:num(v, f'weights.{k}') for k,v in weights.items()}
    if any(v < 0 for v in weights.values()) or sum(weights.values())<=0:
        raise ValueError('weights must be nonnegative, with positive total')
    def from_forecast(case, name, default=None):
        return num(forecasts.get(case,{}).get(name,f.get(name,default)),f'{case}.{name}')

    output={}
    for case in ('bear','base','bull'):
        available={}
        ni=from_forecast(case,'normalized_parent_profit_100m')
        book=from_forecast(case,'parent_equity_100m')
        fcf=from_forecast(case,'normalized_fcff_100m')
        ebitda=from_forecast(case,'normalized_ebitda_100m')
        debt=from_forecast(case,'net_debt_100m')
        minorities=from_forecast(case,'minority_interest_100m',0) or 0
        senior=from_forecast(case,'other_senior_claims_100m',0) or 0
        case_shares=num(forecasts.get(case,{}).get('shares_100m',shares),f'{case}.shares_100m')
        if case_shares is None or case_shares<=0: raise ValueError(f'{case}: shares must be positive')
        if not financial_sector and ni is not None and ni>0 and case in a.get('pe',{}):
            m=num(a['pe'][case], f'pe.{case}')
            if m is not None and m>0: available['pe']=ni*m
        if book is not None and book>0 and case in a.get('pb',{}):
            m=num(a['pb'][case], f'pb.{case}')
            if m is not None and m>0: available['pb']=book*m
        if not financial_sector and ebitda is not None and ebitda>0 and debt is not None and case in a.get('ev_ebitda',{}):
            m=num(a['ev_ebitda'][case],f'ev_ebitda.{case}')
            if m is not None and m>0:
                val=m*ebitda-debt-minorities-senior
                if val>0: available['ev_ebitda']=val
                else: warnings.append(f'{case}: EV/EBITDA equity <= 0 excluded')
        if not financial_sector and 'sotp' in a and case in a['sotp'] and debt is not None:
            part=a['sotp'][case]
            segments=part.get('segments',[])
            if segments:
                vs=[num(seg.get('enterprise_value_100m'),f'sotp.{case}.segments.{i}') for i,seg in enumerate(segments)]
                if any(v is None or v<0 for v in vs):raise ValueError(f'{case}: invalid SOTP segment value')
                overhead=num(part.get('unallocated_adjustment_100m',0), f'sotp.{case}.unallocated_adjustment_100m') or 0
                val=sum(vs)+overhead-debt-minorities-senior
                if val>0:available['sotp']=val
                else:warnings.append(f'{case}: SOTP equity <= 0 excluded')
        if not financial_sector and 'dcf' in a and case in a['dcf'] and fcf is not None and fcf>0 and debt is not None:
            years=a['dcf'].get('years',5)
            if not isinstance(years,int) or not 2<=years<=15:raise ValueError('DCF years 2..15 integer')
            p=a['dcf'][case]
            growth=num(p.get('growth'),f'dcf.{case}.growth')
            wacc=num(p.get('wacc'),f'dcf.{case}.wacc')
            tg=num(p.get('terminal_growth'),f'dcf.{case}.terminal_growth')
            if None in (growth,wacc,tg) or growth<=-1 or wacc<=tg or wacc<=0:
                raise ValueError(f'Invalid DCF inputs {case}')
            cash=fcf;pv=0.
            for yr in range(1,years+1):
                cash*=(1+growth)
                pv+=cash/(1+wacc)**yr
            value=pv+(cash*(1+tg)/(wacc-tg))/(1+wacc)**years-debt-minorities-senior
            if value>0:available['dcf']=value
            else:warnings.append(f'{case}: DCF equity <= 0 excluded')
        parts={k:round(v,3) for k,v in available.items()}
        selected={k:weights[k] for k in parts if weights.get(k,0)>0}
        sum_weight=sum(selected.values())
        if sum_weight<=0:
            output[case]={'equity_value_100m':None,'per_share_rmb':None,'upside_pct':None,
                          'methods':parts,'weights_applied':{},'shares_100m':case_shares,
                          'confidence_flag':'INSUFFICIENT_MODEL_INPUT'}
        else:
            cap=sum(available[k]*w for k,w in selected.items())/sum_weight
            per_share=cap/case_shares
            output[case]={'equity_value_100m':round(cap,3),'per_share_rmb':round(per_share,3),
                          'upside_pct':round((per_share/price-1)*100,2),'methods':parts,
                          'weights_applied':{k:round(w/sum_weight,4) for k,w in selected.items()},
                          'shares_100m':case_shares,
                          'confidence_flag':('MULTI_METHOD_MODEL' if len(selected)>=2 else 'ONE_METHOD_ONLY')}
            if len(selected)<2:warnings.append(f'{case}: only one applicable valuation model; low confidence')
        if financial_sector:warnings.append(f'{case}: generic PE/DCF/EV EBITDA disabled; PB only is insufficient for full bank/insurance/broker valuation')
    cur_ni=num(f.get('normalized_parent_profit_100m'),'normalized_parent_profit_100m')
    cur_book=num(f.get('parent_equity_100m'),'parent_equity_100m')
    if any(output[x]['per_share_rmb'] is None for x in output):
        warnings.append('At least one scenario has no defensible numerical model; keep null and show conditional thesis instead')
    elif not (output['bear']['per_share_rmb']<=output['base']['per_share_rmb']<=output['bull']['per_share_rmb']):
        warnings.append('Scenario ordering inverted: investigate assumptions, forecasts or dilution')
    if any(k not in forecasts for k in ('bear','base','bull')):
        warnings.append('Some scenarios reuse the same historical normalization; configure scenario_forecasts for operating changes')
    return {
        'company':c,'business_type':business_type,'valuation_as_of':s.get('as_of'),
        'units':{'money':'RMB 100m','price':'RMB/share'},
        'current_market_cap_100m':round(market_cap,3),
        'current_pe':round(market_cap/cur_ni,2) if cur_ni is not None and cur_ni>0 else None,
        'current_pb':round(market_cap/cur_book,2) if cur_book is not None and cur_book>0 else None,
        'cases':output,'warnings':warnings,'scenario_assumptions':a.get('scenario_drivers',{}),
        'scenario_forecasts':forecasts,'scenario_probabilities':a.get('scenario_probabilities'),
        'evidence_status':'NOT_CERTIFIED_BY_CALCULATOR',
        'source_coverage':s.get('source_coverage','Not independently verified by this script'),
        'disclaimer':'Assumption-driven model; no official filing or source content verified by this calculator.'
    }


def esc(x): return html.escape(str(x),quote=True)
def pretty(x,digits=1): return '—' if x is None else f'{x:,.{digits}f}'
def money(x): return '—' if x is None else pretty(x,2)

def bar_chart(title, labels, v1, v2=None, names=('收入','归母净利润'), fmt='亿元'):
    """Self-contained SVG; accurately depicts positive, negative, and zero bars."""
    if not labels:return '<p>无可用数据</p>'
    W,H,x0,plotw=800,270,76,690
    value_lists=[v1] + ([v2] if v2 is not None else [])
    vals=[float(v) for vs in value_lists for v in vs if v is not None]
    lo=min(vals+[0.0]); hi=max(vals+[0.0]); span=hi-lo
    if span==0:span=1
    upper,lower=45,211
    def yy(x):return lower-(float(x)-lo)/span*(lower-upper)
    zeroy=yy(0)
    out=[f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">',
         f'<text x="12" y="20" class="chart-title">{esc(title)}</text>',
         f'<line x1="{x0}" y1="{zeroy:.1f}" x2="{x0+plotw}" y2="{zeroy:.1f}" stroke="#8598b1"/>']
    step=plotw/len(labels); bw=min(36,step/max(1,len(value_lists)+1))
    for i,l in enumerate(labels):
        center=x0+step*(i+0.5)
        for j,vs in enumerate(value_lists):
            value=vs[i]
            if value is None:continue
            value=float(value)
            y=yy(value); top=min(y,zeroy); height=max(abs(y-zeroy),0.7)
            xx=center+(j-len(value_lists)/2)*bw
            color=['#2563eb','#0f766e'][j]
            out.append(f'<rect x="{xx:.1f}" y="{top:.1f}" width="{bw-2:.1f}" height="{height:.1f}" rx="2" fill="{color}"/>')
            value_label_y=(top-4 if value>=0 else min(lower+14,y+15))
            out.append(f'<text x="{xx+bw/2:.1f}" y="{value_label_y:.1f}" text-anchor="middle" class="chart-small">{value:.1f}</text>')
        out.append(f'<text x="{center:.1f}" y="{lower+36:.1f}" text-anchor="middle" class="chart-small">{esc(l)}</text>')
    for j,name in enumerate(names[:len(value_lists)]):
        out.append(f'<circle cx="{x0+j*160}" cy="{H-9}" r="5" fill="{["#2563eb","#0f766e"][j]}"/>')
        out.append(f'<text x="{x0+13+j*160}" y="{H-5}" class="chart-small">{esc(name)} ({esc(fmt)})</text>')
    return ''.join(out)+'</svg>'


def html_report(src,v):
    c=v['company']; trend=src.get('history',[]); peers=src.get('peers',[])
    cases=v['cases']; price=c['close_price_rmb']
    head='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>A股研究报告 · 估值模型</title><style>
    :root{font-family:system-ui,-apple-system,"Microsoft Yahei",sans-serif;color:#14253b;background:#f6f8fc}body{max-width:1130px;margin:0 auto;padding:26px}h1{margin:0 0 6px}h2{font-size:19px;margin:0 0 14px}.muted{color:#64748b}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px;margin:20px 0}.card{background:white;padding:20px;border:1px solid #e1e7f1;border-radius:13px}.big{font-size:25px;font-weight:750;margin:9px 0}.section{margin:26px 0}.chart-title{font-size:16px;font-weight:700;fill:#14253b}.chart-small{font-size:12px;fill:#475569}svg{width:100%;height:auto}table{width:100%;border-collapse:collapse;background:white}th,td{border-bottom:1px solid #e9edf5;padding:12px;text-align:left;font-size:14px}th{background:#edf3fc}.tag{background:#e9eef8;padding:5px 9px;border-radius:9px;display:inline-block}li{margin:6px 0}a{color:#1d4ed8;overflow-wrap:anywhere}.notice{border-left:4px solid #f59e0b;background:#fffbeb;padding:12px 15px;border-radius:8px}footer{margin:28px 0;color:#64748b;font-size:12px}
    </style></head><body>'''
    rows=[]
    for case, label in [('bear','悲观'),('base','基准'),('bull','乐观')]:
        x=cases[case]
        methods=', '.join(f'{k.upper()} {money(val)}' for k,val in x['methods'].items()) or '无有效模型'
        rows.append(f'<tr><td>{label}</td><td>{money(x["equity_value_100m"])} 亿元</td><td>{money(x["per_share_rmb"])} 元</td><td>{pretty(x["upside_pct"])}%</td><td>{esc(methods)}</td></tr>')
    charts=''
    if trend:
        labels=[str(y.get('year','?')) for y in trend]
        charts+='<div class="card">'+bar_chart('年度收入与归母净利润',labels,[y.get('revenue_100m') for y in trend],[y.get('parent_profit_100m') for y in trend])+'</div>'
        charts+='<div class="card">'+bar_chart('经营现金流与资本开支',labels,[y.get('operating_cf_100m') for y in trend],[y.get('capex_100m') for y in trend],('经营现金流','资本开支'))+'</div>'
    per_price=[price]+[cases[x]['per_share_rmb'] for x in ['bear','base','bull']]
    charts+='<div class="card">'+bar_chart('市价与情景每股估值（元/股）',['市价','悲观','基准','乐观'],per_price,names=('每股价值',),fmt='元/股')+'</div>'
    ps=''.join(f'<tr><td>{esc(p.get("name","?"))}</td><td>{esc(p.get("growth_pct","—"))}</td><td>{esc(p.get("roe_pct","—"))}</td><td>{esc(p.get("pe","—"))}</td><td>{esc(p.get("pb","—"))}</td><td>{esc(p.get("source_url","未提供"))}</td></tr>' for p in peers)
    warnings=''.join('<li>'+esc(x)+'</li>' for x in v['warnings']) or '<li>未触发自动模型限制提示（不代表数据已验证）</li>'
    demo_notice=('演示数据全部虚构，不可用于投资。' if src.get('is_fictional_example') else '输入数据和估值假设未被此程序自动核实，引用来源需独立确认。')
    audit=v.get('evidence_audit') or {}
    audit_claims=audit.get('claims',[])
    audits=''.join('<tr><td>'+esc(k.get('claim_id'))+'</td><td>'+esc(k.get('status'))+'</td><td>'+esc('; '.join(k.get('warnings',[])[:3]))+'</td></tr>' for k in audit_claims)
    sources=''.join('<li><a href="'+esc(x.get('url','#'))+'">'+esc(x.get('title','来源'))+'</a> / 披露 '+esc(x.get('published_at','未填'))+'</li>' for x in src.get('sources',[])) or '<li>输入未附来源，不能视作可靠研究</li>'
    drivers=''.join('<tr><td>'+esc({'bear':'消极','base':'中性','bull':'积极'}[k])+'</td><td>'+esc(v['scenario_assumptions'].get(k,'未提供量化情景驱动'))+'</td></tr>' for k in ['bear','base','bull'])
    body=f'''<header><span class="tag">研究模型 · 输入真实性未自动核实</span><h1>{esc(c.get('name','?'))} <small>{esc(c.get('ticker',''))}</small></h1><p class="muted">{esc(src.get('industry','行业待核实'))} · 研究日期 {esc(src.get('as_of','未提供'))} · 报价截至 {esc(c.get('price_date','未提供'))} · 所有价值数据单位见表</p></header>
    <div class="notice"><b>注意：</b>{esc(demo_notice)}这里的图和目标价仅反映输入和模型假设，不代表财报及价格已被验证。</div>
    <div class="grid"><div class="card"><div class="muted">收盘价</div><div class="big">¥{money(price)}</div><div class="muted">元/股</div></div><div class="card"><div class="muted">总市值</div><div class="big">{money(v['current_market_cap_100m'])}</div><div class="muted">亿元</div></div><div class="card"><div class="muted">当前模型 PE</div><div class="big">{pretty(v['current_pe'])}x</div></div><div class="card"><div class="muted">当前模型 PB</div><div class="big">{pretty(v['current_pb'])}x</div></div></div>
    <section class="section"><h2>三情景估值与上行空间</h2><div class="card"><table><thead><tr><th>情景</th><th>合理市值</th><th>每股估值</th><th>相对当前市价的空间</th><th>方法分项（市值亿元）</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>
    <section class="section"><h2>三情景核心经营假设</h2><div class="card"><table><thead><tr><th>情景</th><th>经营假设和风险说明</th></tr></thead><tbody>{drivers}</tbody></table><p>估值按各方法的股权价值口径汇总。各方法的权重及参数应有同行和历史样本依据；模型本身不验证这些依据。</p></div></section>
    <section class="section"><h2>可视化趋势（仅绘制输入的真实数值）</h2><div class="grid">{charts}</div></section>
    <section class="section"><h2>同行对比（必须同口径）</h2><div class="card"><table><thead><tr><th>同行</th><th>收入增长%</th><th>ROE%</th><th>PE</th><th>PB</th><th>数据链接/标识</th></tr></thead><tbody>{ps or '<tr><td colspan="6">未提供可核实同行数据</td></tr>'}</tbody></table></div></section>
    <section class="section"><h2>模型与输入限制</h2><div class="card"><ul>{warnings}</ul><p>基准情景模型权重：{esc(cases['base']['weights_applied'])}。行业合理倍数、股权风险溢价等参数必须由真实同行与历史样本校准。</p></div></section>
    <section class="section"><h2>来源核验状态（仅对输入的元数据进行一致性检查）</h2><div class="card"><p>状态：{esc(v.get('evidence_status','NOT_CHECKED'))}。此核验不能自动证明网页和财报中的内容为真，仍须打开原始来源验证。</p><table><thead><tr><th>claim_id</th><th>检验结果</th><th>待核对事项</th></tr></thead><tbody>{audits or '<tr><td colspan="3">无证据登记表：报告不能作为已核验研究</td></tr>'}</tbody></table></div></section>
    <section class="section"><h2>核心来源（人工提供，需逐条核对）</h2><div class="card"><ul>{sources}</ul></div></section>
    <footer>生成时间（运行环境本地时间）{dt.datetime.now().astimezone().isoformat(timespec='seconds')} | 非实时行情、非投资建议、非事实认证。</footer>'''
    return head+body+'</body></html>'


def main():
    parser=argparse.ArgumentParser(description='Offline assumption-driven A-share valuation and visual report generator')
    parser.add_argument('--input',required=True)
    parser.add_argument('--outdir',required=True)
    parser.add_argument('--evidence',help='Optional evidence claim ledger JSON to assess source metadata')
    parser.add_argument('--strict-evidence',action='store_true',help='Fail if evidence is absent or claim metadata has unresolved blockers')
    args=parser.parse_args()
    src=json.loads(Path(args.input).read_text(encoding='utf-8'))
    result=valuation(src)
    if args.evidence:
        from check_evidence import assess
        manifest=json.loads(Path(args.evidence).read_text(encoding='utf8'))
        evidence_audit=assess(manifest)
        if args.strict_evidence and evidence_audit['not_ready_claim_ids']:
            raise SystemExit('Strict source metadata gate failed: '+', '.join(evidence_audit['not_ready_claim_ids']))
        result['evidence_audit']=evidence_audit
        result['evidence_status']=('METADATA_GATE_PASSED_NOT_FACT_VERIFIED' if not evidence_audit['not_ready_claim_ids'] else 'UNRESOLVED_SOURCE_REVIEW')
    else:
        if args.strict_evidence:raise SystemExit('Strict source metadata gate requires --evidence LEDGER.json')
        result['warnings'].append('No evidence ledger supplied; valuation is an assumption-only draft')
    path=Path(args.outdir);path.mkdir(parents=True,exist_ok=True)
    (path/'valuation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (path/'report.html').write_text(html_report(src,result),encoding='utf-8')
    print('Generated:',path.resolve()/'valuation.json',path.resolve()/'report.html')
    print('Note: computations assume externally verified data and industry-calibrated assumptions.')

if __name__=='__main__': main()
