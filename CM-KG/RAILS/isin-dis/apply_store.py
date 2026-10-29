r"""ISIN disambiguation (2026-10-27) — apply the rule to the live regional stores (the store, not the gate).
Per node: every record file under door/records/ is read; records named in RAILS\door\isin_parents.json get `parent` (Eurex products on de get the
derivative parent load_nodes.py now writes nightly); door/index.json is rebuilt from the record files by RAILS\door\store_index.py and compared with the
index on the store. Prior files are copied first to door-reparented/<UTC date>/ (records/<EX>/<code>.pre.json, index.pre.json); nothing deleted.
Writes apply-<label>-<stamp>.json beside (per node: records re-parented, index diff). --dry reads and reports only.
Usage: python -X utf8 -I apply_store.py <label> [--dry] cc [cc …] | all"""
import json, os, sys, datetime, collections, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'door')]; import store, store_index
from azure.storage.blob import ContentSettings
P = json.load(open(os.path.join(HERE, '..', 'door', 'isin_parents.json'), encoding='utf-8'))
label = sys.argv[1]; dry = '--dry' in sys.argv; want = [a for a in sys.argv[2:] if not a.startswith('--')]
if want == ['all']: want = sorted(store.NODES)
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%MZ'); day = stamp[:10]
JS = ContentSettings(content_type='application/json')
DRV = 'an ISIN resolves to the primary listing record; a derivative keeps its own identifiers and never answers an ISIN lookup on its own (2026-10-27)'
def diff(a, b):
    out = {}
    for kind in ('ticker', 'isin', 'lei', 'alias', 'name', 'cmr'):
        A, B = a.get(kind) or {}, b.get(kind) or {}
        ch = [i for i in set(A) | set(B) if A.get(i) != B.get(i)]
        st = [i for i in ch if set(A.get(i) or []) != set(B.get(i) or [])]   # beyond a key listed twice
        out[kind] = {'changed': len(ch), 'set_changed': len(st), 'gone': sum(1 for i in ch if i not in B), 'new': sum(1 for i in ch if i not in A), 'examples': [[i, A.get(i), B.get(i)] for i in sorted(st)[:5]]}
    out['keys'] = {'before': len(a.get('keys') or []), 'after': len(b.get('keys') or []), 'distinct_before': len(set(a.get('keys') or []))}
    return out
def one(cc):
    node = f'{cc}-cm-kg'; c = store.cont(cc); mine = P.get(node) or {}
    cur = store.bj(c, 'door/index.json')
    # only the files the live index serves (its CMR addresses): uploads overwrite but never delete, so a store keeps files of records no longer built
    served = {f"{k.split('/')[1]}/{store_index.slug(k.split('/', 2)[2])}".upper() for k in (cur.get('cmr') or {})} | {f"{k.split('/')[1]}/{store_index.slug(k.split('/', 2)[2])}".upper() for k in cur.get('keys') or []}
    allf = [b.name for b in c.list_blobs(name_starts_with='door/records/') if b.name.endswith('.json')]
    names = [n for n in allf if f"{n.split('/')[2]}/{n.split('/')[3][:-5]}".upper() in served]
    def rd(n): return n, json.loads(c.download_blob(n).readall())
    with cf.ThreadPoolExecutor(32) as ex: recs = dict(ex.map(rd, names))
    # and the folded listing lines the served records name (their files serve the primary; the old rebuild lost their addresses)
    lines = {f"{l['exchange']}/{store_index.slug(l['code'])}".upper() for r in recs.values() for l in r.get('listings') or [] if l.get('cmr', '').startswith(node + '/')}
    extra = [n for n in allf if n not in recs and f"{n.split('/')[2]}/{n.split('/')[3][:-5]}".upper() in lines]
    with cf.ThreadPoolExecutor(32) as ex: recs.update(dict(ex.map(rd, extra)))
    names = names + extra
    changed = []
    for n, r in recs.items():
        if r.get('cmr', '').split('/')[1:2] == ['EUREX'] and n.split('/')[2] == 'EUREX' and not r.get('parent'):
            idn = r.get('identity') or {}; ui = idn.get('underlying_isin') or idn.get('isin') or {}; uc = idn.get('underlying_cmr') or {}
            r['parent'] = {'cmr': uc.get('value'), 'relation': 'derivative', 'isin': ui.get('value'), 'source_url': uc.get('source_url') or ui.get('source_url'), 'read_by': uc.get('read_by') or ui.get('read_by'), 'rule': DRV}
            changed.append(n)
        p = mine.get(r.get('cmr')) if store_index.slug(r.get('cmr', '').split('/', 2)[-1]) == n.split('/')[3][:-5] and r.get('cmr', '').split('/')[1:2] == [n.split('/')[2]] else None
        if p and any((r.get('parent') or {}).get(k) != v for k, v in p.items()):
            r['parent'] = dict(r.get('parent') or {}, **p)
            if n not in changed: changed.append(n)
    # The live index is patched, not replaced (an after-gate step writes entries a rebuild from files does not make, e.g. us 'TXSE:CECO'):
    # every list holds a key once; a record with a parent leaves the ISIN lists; a folded line's ticker and CMR resolve to its primary.
    # store_index.build (the nightly path) is run beside as the check: the two must agree on every ISIN.
    new = json.loads(json.dumps(cur))
    for kind, m in new.items():
        if kind == 'keys': new['keys'] = list(dict.fromkeys(m)); continue
        if isinstance(m, dict):
            for i, ks in m.items():
                if isinstance(ks, list): m[i] = list(dict.fromkeys(ks))
    isn = new.setdefault('isin', {})
    for n, r in recs.items():
        own = (r.get('cmr', '').split('/')[1], store_index.slug(r.get('cmr', '').split('/', 2)[-1])) == (n.split('/')[2], n.split('/')[3][:-5])
        if own and r.get('parent'):
            for m, ids in ((isn, {((r.get('identity') or {}).get('isin') or {}).get('value'), r['parent'].get('isin')}),
                           (new.setdefault('lei', {}), {((r.get('identity') or {}).get('lei') or {}).get('value')})):   # DOORS-06: the LEI follows the ISIN rule
                for i in ids - {None}:
                    i = str(i).upper()
                    if r['cmr'] in (m.get(i) or []):
                        m[i] = [k for k in m[i] if k != r['cmr']]
                        if not m[i]: m.pop(i)
        if own:
            for l in r.get('listings') or []:
                if l.get('cmr') and l['cmr'] != r['cmr'] and l['cmr'].startswith(node + '/'):
                    for kind, ident in (('cmr', l['cmr'].upper()), ('ticker', str(l['code']).upper()), ('ticker', str(l['code']).split('.')[0].upper())):
                        lst = new.setdefault(kind, {}).setdefault(ident, [])
                        if r['cmr'] not in lst: lst.append(r['cmr'])
                    if l['cmr'] in new['keys']: new['keys'].remove(l['cmr'])
    chk = store_index.build((n.split('/')[2], n.split('/')[3][:-5], r) for n, r in recs.items())
    disagree = [f'{kd}:{i}' for kd in ('isin', 'lei') for i in set(new[kd]) | set(chk[kd]) if set(new[kd].get(i) or []) != set(chk[kd].get(i) or [])]
    d = diff(cur, new); d['nightly_builder_isin_disagree'] = {'count': len(disagree), 'examples': sorted(disagree)[:5]}
    rep = {'node': node, 'records': len(recs), 'files_not_served': len(allf) - len(names), 'reparented': len(changed), 'by_relation': dict(collections.Counter((recs[n]['parent'] or {}).get('relation') for n in changed)), 'index_diff': d,
           'isin_multi_after': sum(1 for ks in new['isin'].values() if len(ks) > 1), 'lei_multi_before': sum(1 for ks in (cur.get('lei') or {}).values() if len(set(ks)) > 1), 'lei_multi_after': sum(1 for ks in new['lei'].values() if len(ks) > 1), 'isin_multi_before': sum(1 for ks in (cur.get('isin') or {}).values() if len(ks) > 1)}
    if not dry and (changed or cur != new):
        def cp(n): c.upload_blob(f"door-reparented/{day}/{n[len('door/'):][:-5]}.pre.json", c.download_blob(n).readall(), overwrite=True, content_settings=JS)
        with cf.ThreadPoolExecutor(32) as ex: list(ex.map(cp, changed))
        def up(n): c.upload_blob(n, json.dumps(recs[n], ensure_ascii=False, separators=(',', ':')).encode(), overwrite=True, content_settings=JS)
        with cf.ThreadPoolExecutor(32) as ex: list(ex.map(up, changed))
        c.upload_blob(f'door-reparented/{day}/index.pre.json', c.download_blob('door/index.json').readall(), overwrite=True, content_settings=JS)
        c.upload_blob('door/index.json', json.dumps(new, separators=(',', ':')).encode(), overwrite=True, content_settings=JS)
        rep['written'] = True
    return cc, rep
rows = {}
with cf.ThreadPoolExecutor(6) as ex:
    for cc, r in ex.map(one, want):
        rows[cc] = r; d = r['index_diff']
        print(f"{cc}: files {r['records']} (+{r['files_not_served']} not served) · re-parented {r['reparented']} {r['by_relation']} · keys {d['keys']['before']}->{d['keys']['after']} · set changes " + ', '.join(f"{k} {d[k]['set_changed']}" for k in ('isin', 'ticker', 'cmr', 'lei', 'name', 'alias')) + f" · builder disagrees {d['nightly_builder_isin_disagree']['count']} · isin multi {r['isin_multi_before']}->{r['isin_multi_after']} · lei multi {r['lei_multi_before']}->{r['lei_multi_after']}{' · WRITTEN' if r.get('written') else ''}", flush=True)
json.dump(rows, open(os.path.join(HERE, f'apply-{label}-{stamp}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
