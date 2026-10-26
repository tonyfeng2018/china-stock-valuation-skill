#!/usr/bin/env python3
"""Offline provenance consistency checks. Not a web fact checker.
Records are metadata supplied by an analyst; the program cannot verify page content.
"""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

PRIMARY = {'official_filing', 'regulator', 'government', 'exchange', 'company_ir'}
SECONDARY = {'licensed_vendor', 'structured_vendor', 'industry_association', 'peer_filing', 'broker_research'}
MEDIA = {'media', 'social', 'rumor'}


def check_claim(c, tolerance=0.01):
    warnings = []
    structural_conflict = False
    original = c.get('value')
    ctype = c.get('claim_type', 'other')
    typ = c.get('value_type', 'numeric' if isinstance(original, (float, int)) and not isinstance(original, bool) else 'text')
    grouped = defaultdict(list)
    sources = c.get('sources', [])
    for i, s in enumerate(sources):
        url = s.get('url', '')
        if not url or urlsplit(url).scheme != 'https' or not urlsplit(url).netloc:
            warnings.append(f'source[{i}]: missing HTTPS origin URL')
        kind = s.get('kind', 'unknown')
        # Reprints / syndications must share an origin id. Unknown media origins never count as independent.
        origin = s.get('origin_id')
        if not origin:
            if kind in MEDIA:
                origin = 'unresolved_media_origin'
                warnings.append(f'source[{i}]: media origin unresolved; cannot count as independent corroboration')
            else:
                origin = f'unresolved:{i}'
                warnings.append(f'source[{i}]: explicit original origin_id required for provenance')
        grouped[origin].append(s)
        if not s.get('published_at'):
            warnings.append(f'source[{i}]: missing publication timestamp')
        if c.get('period_end') and s.get('period_end') and s['period_end'] != c['period_end']:
            warnings.append(f'source[{i}]: mismatched financial period')
            structural_conflict = True
        if c.get('unit') and s.get('unit') and s['unit'] != c['unit']:
            warnings.append(f'source[{i}]: mismatched units')
            structural_conflict = True
    unique = [ss[0] for ss in grouped.values()]
    kinds = {s.get('kind', '') for s in unique}
    has_primary = bool(kinds & PRIMARY)
    independent = len(unique)
    has_nonmedia_secondary = bool(kinds & SECONDARY)
    if not sources:
        status = 'UNSUPPORTED'
        warnings.append('No sources supplied')
    elif ctype in {'financial', 'policy', 'official_action'} and not has_primary:
        status = 'NEEDS_PRIMARY'
        warnings.append('Authoritative primary source required for this claim type')
    elif independent < 2:
        status = 'SINGLE_ORIGIN'
        warnings.append('Less than two independently originated sources')
    elif not has_primary and not has_nonmedia_secondary:
        status = 'MEDIA_ONLY'
        warnings.append('No primary or specialist secondary source; media reports do not establish fact')
    else:
        status = 'METADATA_CORROBORATED'
    if structural_conflict: status = 'CONFLICT'
    comparisons = []
    if typ == 'numeric':
        if isinstance(original, bool) or not isinstance(original, (float, int)) or not math.isfinite(original):
            status = 'UNSUPPORTED'
            warnings.append('Expected finite claim numeric value')
        else:
            for o, group in grouped.items():
                numbers = [x.get('value') for x in group if isinstance(x.get('value'), (float, int)) and not isinstance(x.get('value'), bool)]
                if numbers:
                    v = numbers[0]
                    denom = max(abs(float(original)), abs(float(v)), 1e-8)
                    delta = abs(float(v) - float(original)) / denom
                    comparisons.append({'origin_id':o, 'value':v, 'relative_difference':round(delta, 6)})
                    if delta > tolerance:
                        status = 'CONFLICT'
                        warnings.append(f'{o} differs from claim by {delta:.2%}')
                else:
                    warnings.append(f'{o} has no comparable numeric value')
            if len(comparisons) < 2 and status == 'METADATA_CORROBORATED':
                status = 'INCOMPLETE_VALUES'
                warnings.append('Not enough independent comparable numeric observations')
    return {'claim_id':c.get('id', 'UNNAMED'), 'status':status, 'independent_origin_count':independent,
            'primary_source_present':has_primary, 'comparison':comparisons, 'warnings':warnings,
            'caveat':'Metadata-only checking; URLs and facts must be opened/verified independently. Never auto-certify claims.'}


def assess(manifest, tolerance=0.01):
    claims = manifest.get('claims', [])
    ids = [x.get('id') for x in claims]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate claim ids in evidence ledger')
    result = [check_claim(c, tolerance) for c in claims]
    blockers = [r['claim_id'] for r in result if r['status'] != 'METADATA_CORROBORATED']
    return {'assessment_type':'offline_metadata_consistency_only', 'claims':result,
            'summary':{'total':len(result),'metadata_corroborated':len(result)-len(blockers),'requires_review':len(blockers)},
            'not_ready_claim_ids':blockers}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--tolerance',type=float,default=0.01)
    a=ap.parse_args()
    if a.tolerance<0 or a.tolerance>0.5: raise ValueError('Tolerance must be within 0..0.5')
    result=assess(json.loads(Path(a.input).read_text(encoding='utf8')), a.tolerance)
    p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result['summary'],ensure_ascii=False))

if __name__=='__main__':main()
