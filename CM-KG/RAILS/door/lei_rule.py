r"""lei_rule.py — DOORS-05 (CEO order 2026-10-26): the LEI on a served record is filled by ISIN lookup first.
Source: the GLEIF ISIN-to-LEI mapping file (https://mapping.gleif.org/api/v2/isin-lei/latest/download, daily zip), read once per run, kept only for the
node's own ISINs and LEIs. Per record with an ISIN:
  1. the ISIN maps to one LEI          -> identity.lei = that LEI, state sourced, source the mapping file, read date on the field (a name-matched value it
                                          replaces rides in `replaced`) — unless the mapped LEI belongs to a subsidiary of the issuer (IW-01, CEO 2026-10-26):
                                          when GLEIF's relationship records give the mapped LEI's direct or ultimate parent as the record's own LEI (the current
                                          value, or the one this rule replaced), the issuer's own LEI stays (state sourced, source the GLEIF parent record, read
                                          date on the field) and the mapped subsidiary rides in `mapped_subsidiary`
  2. the ISIN maps to several LEIs     -> the current LEI stays if it is one of them (state sourced); otherwise it stays as filled, noted
  3. the ISIN has no GLEIF mapping     -> a current LEI is kept only as filled (never confirmed), with the reason — unless GLEIF maps that LEI to an ISIN
                                          another record on this node holds: then the LEI is that issuer's, and the field is blanked with the reason
The index's lei map follows the record. Called by fold_listings.py (nightly, before the fold) and by itself for a store: python lei_rule.py <cc> --store [--dry]."""
import os, io, csv, json, zipfile, datetime, urllib.request, tempfile
URL = 'https://mapping.gleif.org/api/v2/isin-lei/latest/download'
READ_BY = 'GLEIF ISIN-to-LEI mapping file (daily), LEI by exact ISIN'
API = 'https://api.gleif.org/api/v1/lei-records'; SUB_READ_BY = "GLEIF relationship records (the ISIN's mapped LEI is a subsidiary of this issuer)"
_PAR = {}
def parents(lei):
    """the direct and ultimate parent LEIs GLEIF records for `lei` (Level 2, the public API); {} when it reports none or cannot be read"""
    if lei in _PAR: return _PAR[lei]
    out = {}
    for rel in ('direct-parent', 'ultimate-parent'):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(f'{API}/{lei}/{rel}', headers={'User-Agent': 'Allooloo cm-kg lei_rule (mk@allooloo.ai)', 'Accept': 'application/vnd.api+json'}), timeout=30))
            pid = (d.get('data') or {}).get('id')
            if pid: out[rel] = pid
        except Exception: pass
    _PAR[lei] = out; return out
_CACHE = os.path.join(tempfile.gettempdir(), 'gleif-isin-lei-' + datetime.date.today().isoformat() + '.zip')
def mapping(isins, leis):
    if not os.path.exists(_CACHE):
        urllib.request.urlretrieve(URL, _CACHE + '.part'); os.replace(_CACHE + '.part', _CACHE)
    z = zipfile.ZipFile(_CACHE); rd = csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding='utf-8')); next(rd)
    by_isin, by_lei = {}, {}
    for lei, isin in rd:
        if isin in isins: by_isin.setdefault(isin, set()).add(lei)
        if lei in leis: by_lei.setdefault(lei, set()).add(isin)
    return by_isin, by_lei, datetime.datetime.fromtimestamp(os.path.getmtime(_CACHE), datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
v = lambda r, f: ((r.get('identity') or {}).get(f) or {}).get('value')
RIDS = ('corporate_number', 'cik', 'companies_house_number', 'kvk_number', 'siren', 'uid', 'acn', 'uen', 'register_number', 'business_registration_number', 'sedar_profile')
def apply(node, index, keys, get, put, plan, workers=1):
    if workers > 1:
        import concurrent.futures as cf
        with cf.ThreadPoolExecutor(workers) as ex: recs = dict(zip(keys, ex.map(get, keys)))
    else: recs = {k: get(k) for k in keys}
    recs = {k: r for k, r in recs.items() if r and v(r, 'isin')}
    isins = {v(r, 'isin').upper() for r in recs.values()}; leis = {v(r, 'lei') for r in recs.values() if v(r, 'lei')}
    by_isin, by_lei, read_at = mapping(isins, leis)
    holder = {}
    for k, r in recs.items(): holder.setdefault(v(r, 'isin').upper(), []).append(k)
    out = {'sourced': 0, 'replaced': 0, 'kept_filled': 0, 'blanked': 0, 'no_lei': 0}; changes = []
    for k, r in recs.items():
        isin = v(r, 'isin').upper(); cur = v(r, 'lei'); f = dict((r.get('identity') or {}).get('lei') or {}); M = by_isin.get(isin) or set(); new = None
        if len(M) == 1:
            new_v = next(iter(M))
            own = cur if cur and cur != new_v else ((f.get('replaced') or {}).get('value') if f.get('read_by') == READ_BY and (f.get('replaced') or {}).get('value') != new_v else None)
            par = parents(new_v) if own else {}
            if own and own in par.values():   # IW-01: the issuer's own LEI wins over a mapping to its subsidiary
                rel = 'direct-parent' if par.get('direct-parent') == own else 'ultimate-parent'
                if cur == own and f.get('read_by') == SUB_READ_BY and (f.get('mapped_subsidiary') or {}).get('value') == new_v: out['own_over_subsidiary'] = out.get('own_over_subsidiary', 0) + 1; continue
                new = {'value': own, 'source_url': f'{API}/{new_v}/{rel}', 'read_by': SUB_READ_BY, 'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'state': 'sourced',
                       'mapped_subsidiary': {'value': new_v, 'source_url': f'{URL} (ISIN {isin})', 'read_at': read_at, 'relationship': rel},
                       'note': f'GLEIF maps ISIN {isin} to {new_v}, whose {rel.replace("-", " ")} in GLEIF is {own} (this issuer): the issuer’s own LEI stands (IW-01 rule)'}
                if f.get('replaced') or (cur and cur != own): new['restored_from'] = {'value': cur, 'read_by': f.get('read_by'), 'state': f.get('state')}
                out['own_over_subsidiary'] = out.get('own_over_subsidiary', 0) + 1
                r['identity']['lei'] = new; put(k, r); changes.append({'cmr': k, 'from': cur, 'to': own, 'state': 'sourced', 'rule': 'own over subsidiary'})
                lm = index.setdefault('lei', {})
                if cur and cur != own and isinstance(lm.get(cur), list) and k in lm[cur]:
                    lm[cur] = [x for x in lm[cur] if x != k]
                    if not lm[cur]: lm.pop(cur)
                lm.setdefault(own, []); k in lm[own] or lm[own].append(k)
                continue
            new = {'value': new_v, 'source_url': f'{URL} (ISIN {isin})', 'read_by': READ_BY, 'read_at': read_at, 'state': 'sourced'}
            if cur and cur != new_v: new['replaced'] = {'value': cur, 'read_by': f.get('read_by'), 'state': f.get('state')}; new['note'] = 'ISIN-first rule (DOORS-05): the mapped LEI replaces the value that came by name; the replaced value is kept here for review'; out['replaced'] += 1
            else: out['sourced'] += 1
            if cur == new_v and f.get('read_by') == READ_BY: continue
        elif len(M) > 1:
            if cur in M: new = {**f, 'state': 'sourced', 'note': f'the ISIN maps to {len(M)} LEIs in GLEIF; this one is among them'} if f.get('state') != 'sourced' else None
            elif cur: new = {**f, 'state': 'filled', 'note': f'the ISIN maps to {len(M)} other LEIs in GLEIF; this value came by name'}; out['kept_filled'] += 1
        elif cur:
            others = [h for i2 in (by_lei.get(cur) or set()) for h in holder.get(i2.upper(), []) if h != k]
            # blank only when the register proves two issuers: both records carry a register id and the ids differ (a buy-back or second line of the
            # same company keeps the LEI, as filled, with the note)
            # on jp the TSE code is the JPX listed-company number (one code, one company), so it stands as the register id there
            rid = lambda kk: next((v(recs[kk], f) for f in RIDS if v(recs[kk], f)), None) if not node.startswith('jp-') else 'JPX ' + kk.split('/')[2]
            proven = [o for o in others if rid(o) and rid(k) and rid(o) != rid(k)]
            if others and not proven and f.get('state') != 'filled':
                new = {**f, 'state': 'filled', 'note': f"GLEIF maps this LEI to {', '.join(sorted(by_lei[cur]))}, held on this node by {', '.join(o.split('/', 1)[1] for o in others[:3])}; no register id proves a second issuer"}; out['kept_filled'] += 1
            elif proven:
                new = {'value': None, 'state': None, 'read_at': read_at, 'source_url': f'{URL} (LEI {cur})', 'read_by': READ_BY,
                       'reason': f"GLEIF maps LEI {cur} to {', '.join(sorted(by_lei[cur]))}, held on this node by {', '.join(o.split('/', 1)[1] for o in proven[:3])} (another issuer: register id {rid(proven[0])} vs {rid(k)}); this record's ISIN {isin} has no GLEIF mapping",
                       'replaced': {'value': cur, 'read_by': f.get('read_by'), 'state': f.get('state')}}; out['blanked'] += 1
            elif f.get('state') != 'filled':
                new = {**f, 'state': 'filled', 'note': 'filled by name match; the ISIN has no GLEIF ISIN-to-LEI mapping (DOORS-05 rule: never confirmed)'}; out['kept_filled'] += 1
        else: out['no_lei'] += 1
        if new is None: continue
        r['identity']['lei'] = new; put(k, r); changes.append({'cmr': k, 'from': cur, 'to': new.get('value'), 'state': new.get('state')})
        lm = index.setdefault('lei', {})
        if cur and new.get('value') != cur and isinstance(lm.get(cur), list) and k in lm[cur]:
            lm[cur] = [x for x in lm[cur] if x != k]
            if not lm[cur]: lm.pop(cur)
        if new.get('value'): lm.setdefault(new['value'], []); k in lm[new['value']] or lm[new['value']].append(k)
    plan['lei'] = {'counts': out, 'changes': changes[:500], 'changed': len(changes), 'mapping_read_at': read_at}
    return plan
