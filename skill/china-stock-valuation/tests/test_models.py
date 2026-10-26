import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_analysis import valuation, html_report
from compare_snapshots import compare
from check_evidence import assess, check_claim
from llm_research_assist import make_payload


def demo():
    return json.loads((ROOT/'examples'/'demo-company.json').read_text(encoding='utf-8'))

class ModelsTest(unittest.TestCase):
    def test_capitalization_units(self):
        result=valuation(demo())
        self.assertAlmostEqual(result['current_market_cap_100m'],246.0)
        self.assertAlmostEqual(result['current_pe'],round(246/13.2,2))
    def test_scenario_order(self):
        r=valuation(demo())['cases']
        self.assertLess(r['bear']['per_share_rmb'],r['base']['per_share_rmb'])
        self.assertLess(r['base']['per_share_rmb'],r['bull']['per_share_rmb'])
    def test_warning_no_pe(self):
        d=demo();d['financials']['normalized_parent_profit_100m']=-4.0;d['assumptions']['scenario_forecasts']['base']['normalized_parent_profit_100m']=-4.0
        result=valuation(d)
        self.assertNotIn('pe',result['cases']['base']['methods'])
    def test_bank_avoid_generic_dcf(self):
        d=demo();d['business_type']='bank'
        r=valuation(d)
        self.assertNotIn('dcf',r['cases']['base']['methods'])
        self.assertNotIn('pe',r['cases']['base']['methods'])
    def test_change_detector(self):
        d=demo();n=demo();n['financials']['gross_margin_pct']=30.0
        n['company']['close_price_rmb']=17.0
        result=compare(d,n)
        labels=[x['label'] for x in result['alerts']]
        self.assertIn('毛利率',labels)
        self.assertIn('收盘价',labels)
    def test_html_self_contained(self):
        d=demo();h=html_report(d,valuation(d))
        self.assertIn('<svg',h)
        self.assertIn('虚构',h)
        self.assertIn('收盘价',h)

    def test_independent_method_calculation(self):
        d=demo();result=valuation(d)['cases']['base']
        self.assertIn('ev_ebitda',result['methods'])
        self.assertIn('sotp',result['methods'])
        # EBITDA=20*13, -net_debt=-(-8)
        self.assertAlmostEqual(result['methods']['ev_ebitda'],268.0)
        self.assertEqual(result['confidence_flag'],'MULTI_METHOD_MODEL')

    def test_forecast_changes_valuations(self):
        d=demo();one=valuation(d)
        d['assumptions']['scenario_forecasts']['bear']['normalized_parent_profit_100m']=5
        two=valuation(d)
        self.assertLess(two['cases']['bear']['methods']['pe'],one['cases']['bear']['methods']['pe'])

    def test_dilution_reduces_per_share(self):
        d=demo();one=valuation(d)['cases']['base']
        d['assumptions']['scenario_forecasts']['base']['shares_100m']=15
        two=valuation(d)['cases']['base']
        self.assertAlmostEqual(one['equity_value_100m'],two['equity_value_100m'])
        self.assertLess(two['per_share_rmb'],one['per_share_rmb'])

    def test_missing_debt_excludes_ev_models(self):
        d=demo();d['financials'].pop('net_debt_100m')
        for c in ('bear','base','bull'):
            d['assumptions']['scenario_forecasts'][c].pop('net_debt_100m')
        r=valuation(d)['cases']['base']['methods']
        self.assertNotIn('ev_ebitda',r)
        self.assertNotIn('dcf',r)
        self.assertNotIn('sotp',r)

    def test_media_reprints_not_independent(self):
        evidence=json.loads((ROOT/'examples'/'evidence-demo.json').read_text())
        r=assess(evidence)['claims'][1]
        self.assertEqual(r['independent_origin_count'],1)
        self.assertEqual(r['status'],'SINGLE_ORIGIN')

    def test_discrepant_numeric_source(self):
        evidence=json.loads((ROOT/'examples'/'evidence-demo.json').read_text())
        evidence['claims'][0]['sources'][1]['value']=143
        result=check_claim(evidence['claims'][0])
        self.assertEqual(result['status'],'CONFLICT')

    def test_missing_official_policy_source(self):
        c={'id':'policy','claim_type':'policy','value':'政策变化','sources':[
           {'kind':'media','origin_id':'x','url':'https://example.com/a','published_at':'2026-10-01'},
           {'kind':'media','origin_id':'y','url':'https://example.org/b','published_at':'2026-10-02'}]}
        self.assertEqual(check_claim(c)['status'],'NEEDS_PRIMARY')

    def test_llm_payload_is_source_constrained(self):
        msgs=make_payload(valuation(demo()),{'claims':[]})
        self.assertEqual(msgs[0]['role'],'system')
        self.assertIn('不能',msgs[0]['content'])
        self.assertIn('NOT_CERTIFIED_BY_CALCULATOR',msgs[1]['content'])

if __name__=='__main__':unittest.main()
