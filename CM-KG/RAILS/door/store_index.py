r"""store_index.py — ISIN disambiguation (CEO order 2026-10-27): the store's door/index.json, built from the record files as they sit in the store.
The rule: an ISIN resolves to the primary listing record. A derivative, depositary or secondary-venue record keeps its own identifiers (key, ticker, CMR,
name, aliases) and links to the primary by its `parent` field; it never answers an ISIN or (DOORS-06) LEI lookup on its own.
Each record file is keyed by where it sits (records/<EX>/<slug>.json), not only by the cmr written inside it:
  a file whose cmr is another record is a folded listing line (DOORS-03) serving its primary: the line's own ticker and CMR (read from the primary's
  `listings`) resolve to the primary; the line is not a key and adds nothing else
  a record with `parent` is indexed under every identifier except its ISIN and (DOORS-06, 2026-10-27) its LEI: both resolve to the primary
  every list holds a key once
Used by AZURE\provision_region.py upload (nightly) and RAILS\isin-dis\apply_store.py (the live store)."""
import re
def nkey(s): return re.sub(r'[^a-z0-9]+', ' ', str(s).lower().replace('&', ' and ')).strip()
def slug(t): return re.sub(r'[^A-Za-z0-9.\-]', '_', str(t))
def build(items):
    """items: iterable of (exchange folder, file stem, record dict). Returns the index."""
    idx = {'ticker': {}, 'isin': {}, 'lei': {}, 'alias': {}, 'name': {}, 'cmr': {}, 'keys': []}
    def add(kind, ident, key):
        lst = idx[kind].setdefault(ident, [])
        if key not in lst: lst.append(key)
    def tick(t, key):
        add('ticker', t.upper(), key); root = t.split('.')[0].upper()
        if root != t.upper(): add('ticker', root, key)
    for ex, stem, r in items:
        key = r['cmr']; v = lambda x: ((r.get('identity') or {}).get(x) or {}).get('value')
        if (key.split('/')[1], slug(key.split('/', 2)[2])) != (ex, stem):   # a folded listing line: its address resolves to the primary
            line = next((l for l in r.get('listings') or [] if l.get('exchange') == ex and slug(l.get('code')) == stem), None)
            if line: add('cmr', line['cmr'].upper(), key); tick(str(line['code']), key)
            continue
        add('cmr', key.upper(), key); tick(key.split('/', 2)[2], key)
        if (r.get('parent') or {}).get('relation') == 'listing-line': continue   # DOORS-06 tail: a listing line of a primary on another node answers its own ticker and CMR only
        if key not in idx['keys']: idx['keys'].append(key)
        if v('isin') and not r.get('parent'): add('isin', str(v('isin')).upper(), key)
        if v('lei') and not r.get('parent'): add('lei', str(v('lei')).upper(), key)   # DOORS-06: the LEI follows the ISIN rule
        if v('name'): add('name', nkey(v('name')), key)
        for a in r.get('aliases', []) or []:
            if a.get('value'): add('alias', nkey(a['value']), key)
    return idx
