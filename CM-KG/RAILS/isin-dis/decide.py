r"""ISIN disambiguation (2026-10-27) — decide the primary listing record for every ISIN that answers on more than one record, all roster nodes, and write
the parents of record to RAILS\door\isin_parents.json (prior file kept as .pre-<stamp>). Reads the census indexes (idx-<stamp>\ beside, newest) and
cross-records.json (pull_cross.py). Read only on the stores.
The rule: an ISIN resolves to the primary listing record. Derivative, depositary and secondary-venue records keep their own identifiers and link to the
primary by `parent`; they never answer an ISIN lookup on their own. How the primary is read, in order, from what the records' own sources say:
  1 derivative       a Eurex product (de-cm-kg/EUREX/…) is never the primary; its parent is the underlying's primary record when one is decided
  2 source tag       a line its own exchange source marks as a foreign-ISIN line or a trading-only security (SIX 'foreign ISIN, SIX line'; Euronext
                     'foreign ISIN'; HKEX 'Trading-only security (not listed on HKEX)') is a secondary venue: when exactly one record is not so marked, it is primary
  3 home market      otherwise, when exactly one candidate sits on the node whose market is the ISIN's country (GB -> uk), it is primary
  4 hand item        anything else stays as it is and is named (no guess)
Usage: python -X utf8 -I decide.py [--dry]"""
import json, os, glob, sys, datetime, collections
HERE = os.path.dirname(os.path.abspath(__file__)); DOOR = os.path.join(HERE, '..', 'door'); OUT = os.path.join(DOOR, 'isin_parents.json')
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%MZ'); dry = '--dry' in sys.argv
idxd = sorted(glob.glob(os.path.join(HERE, 'idx-*')))[-1]
R = json.load(open(os.path.join(HERE, 'cross-records.json'), encoding='utf-8'))
nodes = {}
for f in glob.glob(os.path.join(idxd, '*-index.json')):
    cc = os.path.basename(f)[:2]; ix = json.load(open(f, encoding='utf-8'))
    nodes[cc] = {i: list(dict.fromkeys(k for k in ks if k.startswith(cc + '-'))) for i, ks in (ix.get('isin') or {}).items()}
HOME = lambda i: 'uk' if i[:2] == 'GB' else i[:2].lower()
RULE = 'an ISIN resolves to the primary listing record; a {rel} record keeps its own identifiers, links to the primary by parent and never answers an ISIN lookup on its own (CEO order 2026-10-27)'
TAGS = ('foreign ISIN', 'Trading-only security')
def tag(k):
    st = ((R.get(k) or {}).get('id') or {}).get('security_type') or ''
    return next((st for t in TAGS if t in st), None)
groups = collections.defaultdict(list)
for cc, m in nodes.items():
    for i, ks in m.items():
        for k in ks: groups[i].append(k)
parents = collections.defaultdict(dict); hand = []; primary_of = {}; by = collections.Counter(); multi = collections.Counter()
for i, ks in sorted(groups.items()):
    if len(ks) < 2: continue
    for k in ks: multi[k.split('-')[0]] += 0
    multi_nodes = sorted({k.split('-')[0] for k in ks})
    for cc in multi_nodes: multi[cc] += 1
    eu = [k for k in ks if '/EUREX/' in k]; cand = [k for k in ks if k not in eu]
    p, basis = None, None
    if len(cand) == 1: p, basis = cand[0], 'the only listing record under this ISIN; the others are Eurex derivatives on it'
    elif cand:
        untagged = [k for k in cand if not tag(k)]
        if len(untagged) == 1: p, basis = untagged[0], 'the other lines are marked by their own exchange source as secondary venues'
        else:
            pool = untagged or cand; home = [k for k in pool if k.split('-')[0] == HOME(i)]
            if len(home) == 1: p, basis = home[0], f'the record on the home market of the ISIN ({i[:2]}, {HOME(i)}-cm-kg); the others are lines on foreign venues'
    if not p and cand:
        hand.append({'isin': i, 'records': cand, 'tags': {k: tag(k) for k in cand}, 'why': 'no single primary read from the records (no source tag, no single home-market record)'})
    if p: primary_of[i] = p
    for k in ks:
        if k == p: continue
        if k in eu: rel = 'derivative'
        elif not p: continue
        else: rel = 'secondary-venue'
        t = tag(k); st = (R.get(k) or {}).get('id') or {}
        ent = {'cmr': p, 'relation': rel, 'isin': i,
               'basis': (f"Eurex product on this ISIN (Eurex Reference Data API, underlying ISIN); primary: {basis}" if rel == 'derivative' and p else
                         'Eurex product on this ISIN; no listing record of the underlying decided on the roster' if rel == 'derivative' else
                         f"this line's own source marks it '{t}'; primary: {basis}" if t else f'primary: {basis}'),
               'rule': RULE.format(rel=rel), 'set_at': stamp}
        parents[f"{k.split('-')[0]}-cm-kg"][k] = ent; by[(k.split('-')[0], rel)] += 1
out = {n: dict(sorted(v.items())) for n, v in sorted(parents.items())}
print('ISINs on more than one record:', sum(1 for ks in groups.values() if len(ks) > 1), '· decided:', len(primary_of), '· hand items:', len(hand))
print('records re-parented:', sum(by.values()), dict(sorted(by.items())))
if not dry:
    if os.path.exists(OUT): os.replace(OUT, OUT + f'.pre-{stamp}')
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump({'stamp': stamp, 'multi_by_node': dict(multi), 'primary_of': primary_of, 'hand': hand, 'by': {f'{a} {b}': c for (a, b), c in by.items()}},
          open(os.path.join(HERE, f'decide-{stamp}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for h in hand[:40]: print('HAND', h['isin'], h['records'])
