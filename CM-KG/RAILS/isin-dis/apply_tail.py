r"""DOORS-06 tail (CEO order 2026-10-27) — the 31 dual primaries. Rule: the home market is primary (the exchange in the issuer's country of incorporation);
where the issuer is incorporated in a third country, the earliest listing is primary. The other listing becomes a listing line on the primary record with
a parent link, never a second record.
Input: tail-decisions.json beside — {isin: {primary: cmr, lines: [cmr …], basis, dates: {cmr: {first_listed, source_url}}}} (written from the sourced
listing dates). Writes the parents of record into RAILS\door\isin_parents.json (prior file kept .pre-<stamp>):
  the other listing's node: {cmr: primary, relation 'listing-line', isin, basis, rule, set_at} — leaves keys, ISIN, LEI, name and alias; answers its own
                            ticker and CMR (the door serves its own jurisdiction's file), carries parent; facts records drop by one (as a fold)
  the primary's node:       {relation 'primary', isin, lines: [the other listing's line, read from its record now, with source and read date]}
Then the live stores (unless --dry): records first copied to door-reparented/<UTC date>/, record, index and facts patched. Writes tail-apply-<stamp>.json.
Usage: python -X utf8 -I apply_tail.py [--dry]"""
import json, os, sys, datetime, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'door')]
import store, store_index
from azure.storage.blob import ContentSettings
JS = ContentSettings(content_type='application/json'); dry = '--dry' in sys.argv
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%MZ'); day = stamp[:10]; now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
PF = os.path.join(HERE, '..', 'door', 'isin_parents.json'); P = json.load(open(PF, encoding='utf-8'))
T = json.load(open(os.path.join(HERE, 'tail-decisions.json'), encoding='utf-8'))
RULE = ('the home market is primary (the exchange in the issuer\'s country of incorporation); where the issuer is incorporated in a third country the earliest '
        'listing is primary; the other listing is a listing line on the primary record with a parent link, never a second record (CEO order DOORS-06 tail, 2026-10-27)')
cc = lambda k: k.split('-')[0]; node = lambda k: f'{cc(k)}-cm-kg'
conts = {}
def cont(c):
    if c not in conts: conts[c] = store.cont(c)
    return conts[c]
def rpath(k): return f"door/records/{k.split('/')[1]}/{store_index.slug(k.split('/', 2)[2])}.json"
def rec(k): return store.bj(cont(cc(k)), rpath(k))
out = {'stamp': stamp, 'isins': {}, 'by_node': collections.Counter()}
writes = collections.defaultdict(dict)   # cc -> {key: record}
for isin, d in sorted(T.items()):
    p = d['primary']; pr = rec(p); lines = []
    for k in d['lines']:
        r = rec(k)
        ln = {'cmr': k, 'node': node(k), 'exchange': k.split('/')[1], 'code': k.split('/', 2)[2], 'type': 'listing', 'name': ((r.get('identity') or {}).get('name') or {}).get('value'),
              'as_of': r.get('as_of'), 'version': r.get('version'), 'kind': r.get('kind'), 'events_url': r.get('events_url'), 'event_count': r.get('event_count'),
              'identity': r.get('identity'), 'aliases': r.get('aliases') or [], 'halt': r.get('halt'), 'folded_into': p,
              'first_listed': (d.get('dates') or {}).get(k), 'line_read_at': now, 'line_read_from': f'{node(k)} regional store ({rpath(k)})'}
        lines.append(ln)
        ent = {'cmr': p, 'relation': 'listing-line', 'isin': isin, 'basis': d['basis'], 'first_listed': (d.get('dates') or {}).get(k), 'primary_first_listed': (d.get('dates') or {}).get(p), 'rule': RULE, 'set_at': stamp}
        P.setdefault(node(k), {})[k] = ent
        r['parent'] = ent; writes[cc(k)][k] = r; out['by_node'][f'{cc(k)} listing-line'] += 1
    pent = {'relation': 'primary', 'isin': isin, 'basis': d['basis'], 'first_listed': (d.get('dates') or {}).get(p), 'lines': lines, 'rule': RULE, 'set_at': stamp}
    P.setdefault(node(p), {})[p] = pent
    L = list(pr.get('listings') or [])
    if not L:
        L = [{'cmr': p, 'exchange': p.split('/')[1], 'code': p.split('/', 2)[2], 'type': 'primary', 'name': ((pr.get('identity') or {}).get('name') or {}).get('value'), 'as_of': pr.get('as_of'),
              'version': pr.get('version'), 'kind': pr.get('kind'), 'events_url': pr.get('events_url'), 'event_count': pr.get('event_count'), 'identity': pr.get('identity'),
              'aliases': pr.get('aliases') or [], 'halt': pr.get('halt'), 'folded_into': None}]
    have = {x['cmr'] for x in L}; L += [x for x in lines if x['cmr'] not in have]
    pr['listings'] = L; pr['listing_rule'] = pr.get('listing_rule') or 'one record per listed company; one listing line per exchange and segment (DOORS-03, 2026-10-26; cross-node lines DOORS-06 tail, 2026-10-27)'
    writes[cc(p)][p] = pr; out['by_node'][f'{cc(p)} primary'] += 1
    out['isins'][isin] = {'primary': p, 'lines': d['lines'], 'basis': d['basis']}
if not dry:
    os.replace(PF, PF + f'.pre-tail-{stamp}'); json.dump({n: dict(sorted(v.items())) for n, v in sorted(P.items())}, open(PF, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for c, recs in sorted(writes.items()):
        k0 = cont(c); ix = store.bj(k0, 'door/index.json'); facts = store.bj(k0, 'door/facts.json'); nd = f'{c}-cm-kg'; n_lines = 0
        k0.upload_blob(f'door-reparented/{day}/index.pre-tail.json', k0.download_blob('door/index.json').readall(), overwrite=True, content_settings=JS)
        k0.upload_blob(f'door-reparented/{day}/facts.pre-tail.json', k0.download_blob('door/facts.json').readall(), overwrite=True, content_settings=JS)
        for k, r in recs.items():
            k0.upload_blob(f"door-reparented/{day}/{rpath(k)[len('door/'):][:-5]}.pre-tail.json", k0.download_blob(rpath(k)).readall(), overwrite=True, content_settings=JS)
            k0.upload_blob(rpath(k), json.dumps(r, ensure_ascii=False, separators=(',', ':')).encode(), overwrite=True, content_settings=JS)
            if (r.get('parent') or {}).get('relation') == 'listing-line':
                n_lines += 1; idn = r.get('identity') or {}
                if k in ix.get('keys', []): ix['keys'] = [x for x in ix['keys'] if x != k]
                for kind in ('isin', 'lei', 'name', 'alias'):
                    for ident, ks in list((ix.get(kind) or {}).items()):
                        if isinstance(ks, list) and k in ks:
                            ks2 = [x for x in ks if x != k]
                            if ks2: ix[kind][ident] = ks2
                            else: ix[kind].pop(ident)
                fn = (facts.get('nodes') or {}).get(nd) or {}
                fn['records'] = int(fn.get('records') or 0) - 1; fn['folded_listing_lines'] = int(fn.get('folded_listing_lines') or 0) + 1
                ex = k.split('/')[1]
                if isinstance(fn.get('records_by_exchange'), dict) and ex in fn['records_by_exchange']: fn['records_by_exchange'][ex] -= 1
        k0.upload_blob('door/index.json', json.dumps(ix, separators=(',', ':')).encode(), overwrite=True, content_settings=JS)
        k0.upload_blob('door/facts.json', json.dumps(facts, indent=1).encode(), overwrite=True, content_settings=JS)
        out.setdefault('written', {})[c] = {'records': len(recs), 'lines_off_facts': n_lines, 'facts_records_now': ((facts.get('nodes') or {}).get(nd) or {}).get('records')}
        print(c, out['written'][c], flush=True)
out['by_node'] = dict(out['by_node']); print(json.dumps(out['by_node']))
json.dump(out, open(os.path.join(HERE, f'tail-apply-{stamp}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
