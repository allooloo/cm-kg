r"""rollup.py — USR-01 (2026-11-11): the per-issuer numbers of the research page, from the newest research drop of a node's pond (pull.py). Pure: reads the drop,
writes CM-KG\RESEARCH\numbers\<cc>.jsonl (one issuer per line, sorted by cmr) and <cc>.manifest.json. No clock value enters a line: two builds over one drop
are byte-identical. A value the market's record does not carry is not_on_record with the record's own reason; nothing is inferred.
  identity     name, ticker, exchange, ISIN, LEI, security type, segment, sector, jurisdiction — each with source page, read date (the field's own, else
               last_seen, else the record version's as_of — the doors' rule) and state
  disclosure   filings in the trailing twelve months to the record's as_of: count, by type, filing days, cadence (median days between filing days), latency
               (days from the latest filing to the as_of), the same three medians for the issuer's exchange and its sector on this node, the latest five lines
  auditor      the record's auditor fields and every auditor_change of the lifecycle index
  lifecycle    listing, delisting, name_change, domicile_change, segment_move lines of the lifecycle index; a type the index does not map is a named gap
  halt         the record's halt flag, as get_ticker states it
  as_of_depth  the node's sealed vintage (history_from, years) and the sealed years that hold this issuer
  coverage, open_research, licensed   the three research row classes; filled by their own rails (coverage.py), licensed is built empty
Records of kind 'reference (derivative product)' are not listed companies and get no page (counted in the manifest).
Usage: python -X utf8 rollup.py <cc> [...] [--out <dir>]"""
import sys, os, json, hashlib, statistics, datetime, collections
POND = r'C:\ALLOOLOO\CM-KG\POND'; OUT = r'C:\ALLOOLOO\CM-KG\RESEARCH\numbers'
SCHEMA = 'research-numbers v0.1 (USR-01, 2026-11-11)'
LICENSED_RULE = 'A licensed row is served only to an agent whose firm holds that licence (licensor, entitlement). No licensed row is loaded.'
day = lambda s: str(s)[:10] if s else None
import re; DATE = re.compile(r'^\d{4}-\d{2}-\d{2}')   # a line dated to the year or month only is not placed in the window
def field(v, cc, rec_as_of):
    if not isinstance(v, dict) or v.get('value') in (None, '', 'not_found'):
        o = {'state': 'not_on_record', 'market': cc}
        if isinstance(v, dict) and v.get('reason'): o['reason'] = v['reason']
        return o
    own = day(v.get('read_at') or v.get('as_of')); seen = day(v.get('last_seen'))
    return {'value': v['value'], 'source': v.get('source_url') or v.get('source'), 'read_date': own or seen or day(rec_as_of), 'read_date_basis': 'the field' if own else 'last_seen' if seen else 'the record version as_of' if rec_as_of else None, 'read_by': v.get('read_by'), 'state': v.get('state') or 'sourced'}
def latest_drop(cc):
    base = os.path.join(POND, f'{cc}-cm-kg', 'research'); ds = [d for d in os.listdir(base) if os.path.exists(os.path.join(base, d, 'node.json'))]
    key = lambda d: (d[:10], int(d[11:] or 1)); return os.path.join(base, sorted(ds, key=key)[-1])
def med(xs): xs = [x for x in xs if x is not None]; return round(statistics.median(xs), 1) if xs else None
def build(cc, out_dir):
    d = latest_drop(cc); node = json.load(open(os.path.join(d, 'node.json'), encoding='utf-8')); CC = cc.upper(); nn = f'{cc}-cm-kg'
    evs = {}
    for l in open(os.path.join(d, 'events.jsonl'), encoding='utf-8'):
        j = json.loads(l); evs[j['cmr']] = j['events']
    life = node.get('lifecycle') or {}; ltypes = life.get('types') or {}; lgaps = life.get('gaps') or {}; by_cmr = collections.defaultdict(lambda: collections.defaultdict(list))
    for t, rows in ltypes.items():
        for r in rows or []: by_cmr[r.get('cmr')][t].append({'date': r.get('date'), 'title': r.get('title'), 'source': r.get('url')})
    bf = node.get('backfill') or None; sealed = node.get('sealed_years') or {}
    rows = []; skipped = 0
    for l in open(os.path.join(d, 'records.jsonl'), encoding='utf-8'):
        rec = json.loads(l)
        if str(rec.get('kind') or '').startswith('reference'): skipped += 1; continue
        cmr = rec['cmr']; idn = rec.get('identity') or {}; as_of = rec.get('as_of'); F = lambda k: field(idn.get(k), CC, as_of)
        to = datetime.date.fromisoformat(as_of); frm = (to - datetime.timedelta(days=365)).isoformat()
        ev = sorted([e for e in evs.get(cmr, []) if isinstance(e.get('date'), str) and frm <= e['date'] <= as_of], key=lambda e: (e['date'], e.get('reference') or '', e.get('url') or '', e.get('title') or ''), reverse=True)
        # the window is the filings door's own rule (date >= from and date <= to, as written on the line), so the count is get_filings' count;
        # a line dated to the year or month only is counted as a filing but is not a filing day
        days = sorted({e['date'][:10] for e in ev if DATE.match(e['date'])}); gaps =[(datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days for a, b in zip(days, days[1:])]
        dis = {'window': {'from': frm, 'to': as_of}, 'filings': len(ev), 'by_type': dict(sorted(collections.Counter(e.get('event_type') or 'untyped' for e in ev).items(), key=lambda x: (-x[1], x[0]))),
               'filing_days': len(days), 'cadence_median_gap_days': med(gaps) if gaps else None, 'latest_filing_date': days[-1] if days else None, 'latency_days': (to - datetime.date.fromisoformat(days[-1])).days if days else None,
               'latest': [{'date': e['date'][:10], 'type': e.get('event_type'), 'category': e.get('category'), 'title': e.get('title'), 'source': e.get('url')} for e in ev[:5]],
               'source': rec.get('events_url'), 'read': 'the node\'s event lines (list_events_since), as get_filings serves them'}
        if not ev: dis['note'] = 'no disclosure line on the record for this issuer in the window'
        halt = rec.get('halt')
        if isinstance(halt, dict) and halt.get('value') is True: status = {'value': 'halted', 'since': halt.get('since'), 'reason': halt.get('reason'), 'source': halt.get('page') or halt.get('source_url'), 'read_date': day(halt.get('read_at'))}
        elif isinstance(halt, dict) and halt.get('value') is False: status = {'value': 'listed, not halted', 'source': halt.get('page') or halt.get('source_url'), 'read_date': day(halt.get('read_at'))}
        else: status = {'value': 'listed', 'note': f"on the {nn} register as of {as_of}; the node's halt flag was not read for this record", 'read_date': day(as_of)}
        lc = by_cmr.get(cmr, {})
        if not life or life.get('register') == 'not mapped yet' and not ltypes: changes = {'state': 'not_on_record', 'market': CC, 'reason': lgaps.get('auditor_change') or f'the lifecycle index of {nn} is not built'}
        elif lgaps.get('auditor_change'): changes = {'state': 'not_on_record', 'market': CC, 'reason': lgaps['auditor_change']}
        else: changes = sorted(lc.get('auditor_change', []), key=lambda x: (x['date'] or '', x['source'] or ''))
        lifecycle = {}
        for t in ('listing', 'delisting', 'name_change', 'domicile_change', 'segment_move'):
            lifecycle[t] = {'state': 'not_on_record', 'market': CC, 'reason': lgaps[t]} if lgaps.get(t) else sorted(lc.get(t, []), key=lambda x: (x['date'] or '', x['source'] or '')) if life else {'state': 'not_on_record', 'market': CC, 'reason': f'the lifecycle index of {nn} is not built'}
        # sealed = what get_as_of serves: the market's Replay split (backfill/replay/). Years sealed in the store with no Replay split are named apart and are
        # not an as-of depth yet (the as-of door answers not_sealed for them).
        served = bool(bf) and bool(sealed); yrs = sorted((bf.get('years') or {}).keys()) if bf else []
        depth = {'sealed': served, 'node_history_from': bf.get('history_from') if served else None, 'node_years_sealed': yrs if served else [], 'issuer_years_sealed': sealed.get(cmr, []), 'live_record_began': bf.get('live_record_began') if bf else None, 'record_version': rec.get('version')}
        if bf and not served: depth['store_years_sealed_not_served'] = yrs; depth['note'] = f'{len(yrs)} years are sealed in the {CC} store; their Replay split is not built, so the as-of door answers not_sealed and the record is the live record as of {as_of}'
        if not bf: depth['note'] = f'the {CC} vintage is not sealed; the record is the live record as of {as_of}'
        o = {'schema': SCHEMA, 'cmr': cmr, 'node': nn, 'market': CC, 'record': {'as_of': as_of, 'version': rec.get('version'), 'url': f"{(rec.get('events_url') or '').split('/events/')[0]}/record/{cmr.split('/', 1)[1]}" if rec.get('events_url') else None},
             'identity': {'name': F('name'), 'ticker': F('ticker'), 'exchange': F('exchange'), 'isin': F('isin'), 'lei': F('lei'), 'security_type': F('security_type'), 'segment': field(idn.get('segment') or idn.get('market_segment'), CC, as_of), 'sector': F('sector'), 'jurisdiction': F('jurisdiction'), 'website': F('website')},
             'status': status, 'disclosure': dis,
             'auditor': {'auditor': F('auditor'), 'auditor_location': F('auditor_location'), 'auditor_firm_id': F('auditor_firm_id'), 'changes': changes},
             'lifecycle': lifecycle, 'as_of_depth': depth,
             'coverage': {'state': 'not_read', 'note': 'the coverage field has not been read for this issuer'}, 'open_research': {'state': 'not_read', 'rows': []},
             'licensed': {'rows': [], 'columns': ['licensor', 'entitlement', 'title', 'date', 'source'], 'rule': LICENSED_RULE}}
        rows.append(o)
    # the peer medians: the issuer's exchange and its sector on this node (five issuers or more; fewer is said)
    def peers(keyf):
        g = collections.defaultdict(list)
        for o in rows:
            k = keyf(o)
            if k: g[k].append(o['disclosure'])
        return {k: {'issuers': len(v), 'median_filings': med([x['filings'] for x in v]), 'median_cadence_gap_days': med([x['cadence_median_gap_days'] for x in v]), 'median_latency_days': med([x['latency_days'] for x in v])} for k, v in g.items()}
    val = lambda o, k: o['identity'][k].get('value'); pe = peers(lambda o: val(o, 'exchange')); ps = peers(lambda o: val(o, 'sector'))
    for o in rows:
        p = {}
        for name, tab, k in (('exchange', pe, val(o, 'exchange')), ('sector', ps, val(o, 'sector'))):
            if not k: p[name] = {'state': 'not_on_record', 'market': CC}
            elif tab[k]['issuers'] < 5: p[name] = {'name': k, 'issuers': tab[k]['issuers'], 'note': 'fewer than five issuers on this node: no median is stated'}
            else: p[name] = {'name': k, **tab[k]}
        o['disclosure']['against'] = p
        o['numbers_hash'] = 'sha256:' + hashlib.sha256(json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    rows.sort(key=lambda o: o['cmr']); os.makedirs(out_dir, exist_ok=True); body = ''.join(json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for o in rows).encode()
    open(os.path.join(out_dir, f'{cc}.jsonl'), 'wb').write(body)
    man = {'node': nn, 'drop': os.path.basename(d), 'record_as_of': (node.get('facts') or {}).get('as_of'), 'issuers': len(rows), 'reference_products_not_paged': skipped, 'event_lines_in_drop': node['counts']['event_lines'], 'sha256': hashlib.sha256(body).hexdigest(), 'schema': SCHEMA}
    json.dump(man, open(os.path.join(out_dir, f'{cc}.manifest.json'), 'w', encoding='utf-8'), indent=1); print(json.dumps(man), flush=True)
a = sys.argv[1:]; out = OUT
if '--out' in a: i = a.index('--out'); out = a[i + 1]; a = a[:i] + a[i + 2:]
bad = 0
for cc in a:
    try: build(cc, out)
    except Exception as e: bad += 1; print(cc, 'FAILED', repr(e)[:300], flush=True)
sys.exit(1 if bad else 0)
