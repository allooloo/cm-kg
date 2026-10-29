r"""enrich_node.py — DAY ORDER 4 (2026-10-24): NODE-HALT-01 + NODE-ISIN-01 on the door data a node job just built (load_nodes.py output, before the
forward-only gate and the upload). One copy in RAILS\door; the us pipeline calls the same functions from its render.
  halt  — the market's own halt / suspension list, read tonight (RAILS\halts\halt_<cc>.py fetch()): every record carries
          "halt": {"value": true|false, "since", "reason", "source_url", "read_by", "read_at", "state": "sourced"}; a list that was not read leaves
          "halt": {"value": null, "state": null, "reason": "<why>"} — never a guessed false. door\halts.json beside the records keeps the night's list.
  isin  — kr only: the KRX standard code (ISIN) per short code (RAILS\isin-fill\kr_isin.py fetch()), written into identity.isin with its source, and
          added to the index's isin map. A record that already carries an ISIN keeps it (the value of record stands; a conflict is noted, not replaced).
Usage: python enrich_node.py <cc> [--data <door data dir>]   (default C:\ALLOOLOO\CM-KG\DOOR\data, i.e. /job/ALLOOLOO/CM-KG/DOOR/data in the image)"""
import os, sys, json, glob, importlib.util, datetime
ROOT = os.environ.get('CMKG_ROOT', r'C:\ALLOOLOO'); RAILS = os.path.join(ROOT, 'CM-KG', 'RAILS')
def load(path, name):
    if not os.path.exists(path): return None
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
PAD = {'hk': 5, 'kr': 6, 'jp': 4}
def norm_code(cc, t):
    t = str(t or '').strip().upper()
    if cc in PAD and t.isdigit(): t = t.zfill(PAD[cc])
    return t
def read_halts(cc):
    m = load(os.path.join(RAILS, 'halts', f'halt_{cc}.py'), f'halt_{cc}')
    if not m: return None, f'no halt reader for {cc}'
    try:
        h = m.fetch()
        if h.get('unavailable') or h.get('note') == 'unavailable': return None, f"halt list unavailable: {h.get('note') or h.get('unavailable')}"
        return h, None
    except Exception as e: return None, f'halt list not read tonight ({type(e).__name__})'
def halt_index(cc, h):
    by_isin, by_code = {}, {}
    for x in (h or {}).get('halted', []):
        if x.get('isin'): by_isin[str(x['isin']).upper()] = x
        if x.get('ticker'): by_code[norm_code(cc, x['ticker'])] = x
    return by_isin, by_code
def halt_field(h, x, why=None):
    if h is None: return {'value': None, 'state': None, 'reason': why}
    base = {'source_url': h.get('source_url'), 'read_by': h.get('read_by'), 'read_at': h.get('read_at'), 'state': 'sourced'}
    if x: return {'value': True, 'since': x.get('since'), 'reason': x.get('reason'), 'page': x.get('page') or h.get('source_url'), **base}
    return {'value': False, **base}
def record_halt(cc, rec, h, idx_isin, idx_code, why):
    ident = rec.get('identity') or {}
    isin = ((ident.get('isin') or {}).get('value') or '').upper()
    code = norm_code(cc, (ident.get('ticker') or {}).get('value') or rec.get('cmr', '').split('/')[-1])
    x = idx_isin.get(isin) if isin else None
    if not x: x = idx_code.get(code)
    return halt_field(h, x, why)
def main():
    cc = sys.argv[1]; node = f'{cc}-cm-kg'
    data = sys.argv[sys.argv.index('--data') + 1] if '--data' in sys.argv else os.path.join(ROOT, 'CM-KG', 'DOOR', 'data')
    files = glob.glob(os.path.join(data, 'records', node, '*', '*.json'))
    h, why = read_halts(cc); ii, ic = halt_index(cc, h)
    kr = {}
    if cc == 'kr':
        m = load(os.path.join(RAILS, 'isin-fill', 'kr_isin.py'), 'kr_isin')
        try: rows = m.fetch() if m else None
        except Exception as e: rows = None; print('kr ISIN list not read:', type(e).__name__)
        if rows: kr = {str(r['code']).zfill(6): (r, rows) for r in rows.get('rows', []) if r.get('isin')}
    idx_path = os.path.join(data, 'index.json'); idx = json.load(open(idx_path, encoding='utf-8')) if os.path.exists(idx_path) else None
    n = halted = isin_added = isin_conflict = 0
    for f in files:
        rec = json.load(open(f, encoding='utf-8')); n += 1
        rec['halt'] = record_halt(cc, rec, h, ii, ic, why); halted += 1 if rec['halt'].get('value') else 0
        if kr:
            code = norm_code('kr', rec.get('cmr', '').split('/')[-1]); hit = kr.get(code)
            ident = rec.setdefault('identity', {}); cur = (ident.get('isin') or {}).get('value')
            if hit:
                r, rows = hit
                if not cur:
                    ident['isin'] = {'value': r['isin'], 'source_url': rows.get('source_url'), 'read_by': 'KRX stock finder (data.krx.co.kr finder_stkisu: full_code = the KRX standard code)', 'state': 'sourced', 'read_at': rows.get('read_at')}; isin_added += 1
                    if idx is not None: idx.setdefault('isin', {}).setdefault(r['isin'], [])
                    if idx is not None:
                        v = idx['isin'][r['isin']]; v = v if isinstance(v, list) else [v]; key = rec.get('cmr')
                        if key and key not in v: v.append(key)
                        idx['isin'][r['isin']] = v
                elif cur != r['isin']: isin_conflict += 1; ident['isin']['conflict'] = {'krx_standard_code': r['isin'], 'source_url': rows.get('source_url')}
        json.dump(rec, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    if idx is not None and kr: json.dump(idx, open(idx_path, 'w', encoding='utf-8'), separators=(',', ':'))
    json.dump({'node': node, 'read_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'list': h, 'not_read': why}, open(os.path.join(data, 'halts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'enrich {node}: records {n} · halted {halted} · halt list {"read" if h else "NOT READ: " + str(why)} · isin added {isin_added} · isin conflicts {isin_conflict}')
if __name__ == '__main__': main()
