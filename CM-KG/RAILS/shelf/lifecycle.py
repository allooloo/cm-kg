r"""SHELF-01 step 1 (Events) — the lifecycle type map per register, and the per-node index events-by-type.json built from the node's event lines.
Lifecycle types: listing · delisting · name_change · domicile_change · auditor_change · segment_move. Each register maps only what its own filings or
bulletins state; a type the register does not state is named as a gap in the map, never guessed. The existing event_type of a line is never changed:
the lifecycle type rides beside it in the index.
  us  (SEC EDGAR):   listing ← Form 8-A12B / 8-A12G (registration of a class on an exchange) and the exchange's certification (CERT…);
                     delisting ← Form 25 / 25-NSE; auditor_change ← 8-K item 4.01 (changes in registrant's certifying accountant);
                     name_change ← 8-K item 5.03 only when the filing's own description names a name change; domicile/segment: gap
  ca  (TSXV / CSE bulletins, wires): listing ← "NEW LISTING" bulletins; delisting ← "DELIST…" bulletins; name_change ← "NAME CHANGE";
                     domicile_change ← "CONTINUANCE" (continued into another jurisdiction); auditor_change ← "change of auditor"; segment_move ←
                     "graduation" / "transfer to NEX" / "transfer to TSX" bulletins
Usage: python -X utf8 -I lifecycle.py build <cc> [--store]      -> events-by-type.json (local data dir, or the node's store door/events-by-type.json)
       python -X utf8 -I lifecycle.py map                         -> prints the maps (the roster copy and the page read them)"""
import os, re, sys, json, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
TYPES = ['listing', 'delisting', 'name_change', 'domicile_change', 'auditor_change', 'segment_move']
MAP = {
 'us': {'register': 'SEC EDGAR (filings under the issuer\'s CIK)',
        'rules': [('listing', 'form', r'^(8-A12B|8-A12G)(/A)?$|^CERT'), ('delisting', 'form', r'^25(-NSE)?(/A)?$'), ('auditor_change', 'item', r'^4\.01$'),
                  ('name_change', 'title', r'(?i)name change|change(d)? (its|the company\'s|our) name')],
        'gaps': {'domicile_change': 'EDGAR states no dated change of state of incorporation on a filing line', 'segment_move': 'the exchanges\' tier transfers are not EDGAR filings'}},
 'ca': {'register': 'TSX Venture Exchange and CSE bulletins; issuer releases on the wires',
        'rules': [('listing', 'title', r'(?i)\bnew listing\b|\blisting of (?:common )?shares\b'), ('delisting', 'title', r'(?i)\bdelist'), ('name_change', 'title', r'(?i)\bname change\b'),
                  ('domicile_change', 'title', r'(?i)\bcontinuance\b'), ('auditor_change', 'title', r'(?i)\bchange of auditor'), ('segment_move', 'title', r'(?i)\bgraduation\b|\btransfer to nex\b|\btransfer to (?:the )?tsx\b')],
        'gaps': {}},
}
def kind_of(cc, e):
    m = MAP.get(cc)
    if not m: return None
    form = (e.get('category') or e.get('title') or '').split(' — ')[0].strip(); title = e.get('title') or ''
    items = re.findall(r'\b\d\.\d\d\b', (re.search(r'\(items ([^)]*)\)', title) or [None, ''])[1])
    for t, field, pat in m['rules']:
        if field == 'form' and re.search(pat, form): return t
        if field == 'item' and form.startswith('8-K') and any(re.match(pat, i) for i in items): return t
        if field == 'title' and re.search(pat, title): return t
    return None
def build(cc, lines_by_key):
    """lines_by_key: {cmr: [event lines]} -> the index {type: [{cmr, date, title, url, source, event_type}]} newest first, plus the map and counts"""
    idx = {t: [] for t in TYPES}
    for k, evs in lines_by_key.items():
        for e in evs:
            t = kind_of(cc, e)
            if t: idx[t].append({'cmr': k, 'date': e.get('date'), 'title': e.get('title'), 'url': e.get('url'), 'source': e.get('source') or e.get('wire'), 'event_type': e.get('event_type')})
    for t in idx: idx[t].sort(key=lambda x: (x['date'] or '', x['cmr']), reverse=True)
    m = MAP.get(cc) or {'register': 'not mapped yet', 'rules': [], 'gaps': {t: 'no lifecycle type map for this register yet (SHELF-01: us and ca first)' for t in TYPES}}
    return {'node': f'{cc}-cm-kg', 'built_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'register': m['register'],
            'type_map': [{'type': t, 'from': f, 'rule': p} for t, f, p in m['rules']], 'gaps': m['gaps'], 'counts': {t: len(v) for t, v in idx.items()}, 'types': idx,
            'note': 'lifecycle type beside each line\'s own event_type (unchanged); a type the register does not state is a gap, never guessed (SHELF-01, 2026-10-27)'}
def main():
    a = sys.argv[1:]
    if a[:1] == ['map']: print(json.dumps(MAP, indent=1)); return
    cc = a[1]
    if '--store' in a:
        sys.path.insert(0, os.path.join(HERE, '..', 'isin-dis')); import store, concurrent.futures as cf
        c = store.cont(cc); names = [b.name for b in c.list_blobs(name_starts_with='door/events/') if b.name.endswith('.json')]
        def rd(n):
            p = n.split('/'); return f'{cc}-cm-kg/{p[2]}/{p[3][:-5]}', json.loads(c.download_blob(n).readall())
        with cf.ThreadPoolExecutor(32) as ex: L = dict(ex.map(rd, names))
        out = build(cc, L)
        if '--dry' not in a:
            if c.get_blob_client('door/events-by-type.json').exists(): c.upload_blob(f"door-shelf/{out['built_utc'][:10]}/events-by-type.pre.json", c.download_blob('door/events-by-type.json').readall(), overwrite=True)
            c.upload_blob('door/events-by-type.json', json.dumps(out, ensure_ascii=False, separators=(',', ':')).encode(), overwrite=True)
    else:
        data = a[2] if len(a) > 2 and not a[2].startswith('--') else os.path.join(os.environ.get('CMKG_ROOT', r'C:\ALLOOLOO'), 'CM-KG', 'DOOR', 'data')
        node = f'{cc}-cm-kg'; base = os.path.join(data, 'events', node); L = {}
        for ex in os.listdir(base) if os.path.isdir(base) else []:
            for fn in os.listdir(os.path.join(base, ex)):
                if fn.endswith('.json'): L[f'{node}/{ex}/{fn[:-5]}'] = json.load(open(os.path.join(base, ex, fn), encoding='utf-8'))
        out = build(cc, L); json.dump(out, open(os.path.join(data, 'events-by-type.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f"{cc}-cm-kg events-by-type: {json.dumps(out['counts'])} · gaps {list(out['gaps'])}")
if __name__ == '__main__': main()
