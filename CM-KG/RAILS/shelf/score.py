r"""SHELF-01 step 3 (Score) — per issuer: cadence, latency, silence; each as the issuer's value, its exchange percentile and its sector percentile.
Numbers and percentiles only: no opinion words, no ratings, no recommendations.
Reads: the node's sealed market-years (the newest manifest of each year, verified by replay_index's rule: signature and hash tree root) plus the live event
lines (door/events). A market is scored only when its ledger entry is complete and every sealed manifest verifies (else: nothing written, named).
  cadence   filings per year, by type — results and statements (event_type results / financial_statement / regulatory filings of results forms)
  latency   days from period end to filing, where the filing states its period end (row period_end; EDGAR rows 'report date …'): median and p90
  silence   the longest gap in days between two consecutive dated lines of the issuer, over the years scored
Writes door/score/<EX>/<code>.json per issuer (signed, kid allooloo-cmr-2026-10) and door/score/_tables.json (exchange and sector distributions).
Scores carry the years available; a market with one sealed year scores on one and says so.
Usage: python -X utf8 -I score.py <cc> [--dry]    (store mode, the live run)
       python -X utf8 score.py <cc> --data <door data dir> --sealed <dir of rows-*.jsonl>   (nightly step; a FAIL never holds the record)"""
import os, sys, json, re, statistics, datetime, collections, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'isin-dis'), os.path.join(HERE, '..', 'door'), os.path.join(HERE, '..', 'backfill')]
RESULTS = {'results', 'financial_statement'}
PERIODIC = re.compile(r'^(10-K|10-Q|10-KT|10-QT|20-F|40-F)(/A)?\b')   # EDGAR forms whose period of report is a period end
RESULT_FORMS = re.compile(r'^(10-K|10-Q|10-KT|20-F|40-F|6-K)(/A)?\b')
def pe_of(r):
    if r.get('period_end'): return r['period_end'][:10]
    if not PERIODIC.match(r.get('category') or r.get('title') or ''): return None   # an 8-K / 6-K 'report date' is the event's date, not a period end (SHELF-01 2026-10-28)
    m = re.search(r'report date (\d{4}-\d{2}-\d{2})', r.get('detail') or '')
    return m.group(1) if m else None
def is_result(r): return r.get('event_type') in RESULTS or bool(RESULT_FORMS.match((r.get('category') or r.get('title') or '')))
def pct(vals, x, lower_better=False):
    v = sorted(vals)
    if not v or x is None: return None
    below = sum(1 for y in v if (y > x if lower_better else y < x)); eq = sum(1 for y in v if y == x)
    return round(100.0 * (below + 0.5 * eq) / len(v), 1)
def p90(v): v = sorted(v); return v[min(len(v) - 1, int(round(0.9 * (len(v) - 1))))] if v else None
def score_market(cc, rows_by_key, sector_of, years):
    out = {}
    for k, rows in rows_by_key.items():
        rows = [{'date': t[0], 'url': t[1], 'event_type': 'results' if t[2] else '', 'period_end': t[3]} if isinstance(t, tuple) else t for t in rows]   # main() passes tuples
        rows = [r for r in rows if r.get('date')]
        if not rows: continue
        res = [r for r in rows if is_result(r)]
        per_year = collections.Counter(r['date'][:4] for r in res)
        cad = round(sum(per_year.values()) / max(1, len(years)), 2)
        lat = sorted(d for d in ((datetime.date.fromisoformat(r['date'][:10]) - datetime.date.fromisoformat(pe_of(r))).days for r in res if pe_of(r)) if 0 <= d <= 400)
        ds = sorted({r['date'][:10] for r in rows}); gaps = [(datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days for a, b in zip(ds, ds[1:])]
        out[k] = {'cadence_results_per_year': cad, 'results_by_year': dict(sorted(per_year.items())), 'latency_days_median': statistics.median(lat) if lat else None, 'latency_days_p90': p90(lat),
                  'latency_filings_with_period_end': len(lat), 'silence_days_longest': max(gaps) if gaps else None, 'lines_scored': len(rows), 'exchange': k.split('/')[1], 'sector': sector_of.get(k)}
    groups = collections.defaultdict(list)
    for k, s in out.items(): groups[('exchange', s['exchange'])].append(k); groups[('sector', s['sector'])].append(k)
    tables = {}
    for (g, name), ks in groups.items():
        if name is None: continue
        tables[f'{g}:{name}'] = {'issuers': len(ks), **{m: sorted(x for x in (out[k][m] for k in ks) if x is not None) for m in ('cadence_results_per_year', 'latency_days_median', 'silence_days_longest')}}
    for k, s in out.items():
        for g in ('exchange', 'sector'):
            t = tables.get(f"{g}:{s[g]}") or {}
            s[f'{g}_percentile'] = {'cadence_results_per_year': pct(t.get('cadence_results_per_year') or [], s['cadence_results_per_year']),
                                    'latency_days_median': pct(t.get('latency_days_median') or [], s['latency_days_median'], lower_better=True),
                                    'silence_days_longest': pct(t.get('silence_days_longest') or [], s['silence_days_longest'], lower_better=True), 'peers': t.get('issuers')}
    return out, tables
def main():
    a = sys.argv[1:]; cc = a[0]; node = f'{cc}-cm-kg'; dry = '--dry' in a
    import store, store_index, backfill as BF
    from replay_index import newest_manifest, year_lines
    import hashlib
    from azure.storage.blob import ContentSettings
    H = json.load(open(os.path.join(HERE, 'hold.json'), encoding='utf-8'))
    if cc in H['markets'] and not (dry and '--proof' in a): print(f'{node}: held — {H["markets"][cc]}'); return 0
    c = store.cont(cc)
    try: led = BF.order_get(cc)
    except Exception as x:   # a node rail job holds no read on the order ledger: the market's own store answers the same test (years done against years needed)
        f = (json.loads(c.download_blob('backfill/facts.json').readall()) if c.get_blob_client('backfill/facts.json').exists() else {}) or {}
        need = BF.years_for(cc, f.get('live_record_began')); done = {int(y) for y in (f.get('years') or {})}
        led = {'complete': bool(f) and set(need) <= done, 'left': sorted(set(need) - done, reverse=True), 'read_from': 'backfill/facts.json (ledger not readable here)'}
    if not (led and led.get('complete')): print(f'{node}: ledger entry not complete ({(led or {}).get("left")}) — not scored'); return 0
    ys = sorted({int(b.name.split('/')[1]) for b in c.list_blobs(name_starts_with='backfill/') if re.match(r'backfill/\d{4}/manifest', b.name)})
    by = collections.defaultdict(list); ix = store.bj(c, 'door/index.json'); cm = ix.get('cmr') or {}; bad = []
    pool = {}; s = lambda v: pool.setdefault(v, v)
    tup = lambda r: (s(r['date'][:10]), s(r.get('url') or ''), is_result(r), pe_of(r))   # SHELF-01 2026-10-27 (us scale): only what scoring reads, strings shared
    for y in ys:
        man = store.bj(c, newest_manifest(c, y)); got = collections.defaultdict(list)
        for _, r in year_lines(c, man):
            k = f"{node}/{r.get('exchange')}/{r.get('ticker')}".upper()
            if k in cm and r.get('date'): got[cm[k][0]].append(tup(r))
        ck = man.pop('_check')
        if not (ck['signature'] and ck['root']): bad.append(y); continue
        for k, v in got.items(): by[k].extend(v)
        del got
    if bad: print(f'{node}: manifests that do not verify {bad} — not scored'); return 0
    names = [b.name for b in c.list_blobs(name_starts_with='door/events/') if b.name.endswith('.json')]
    def rd(n): p = n.split('/'); return f'{node}/{p[2]}/{p[3][:-5]}', json.loads(c.download_blob(n).readall())
    with cf.ThreadPoolExecutor(32) as ex:
        for k, evs in ex.map(rd, names):
            seen = {(t[0], t[1]) for t in by.get(k, [])}
            by[k].extend(tup(e) for e in evs if e.get('date') and (e['date'][:10], e.get('url') or '') not in seen)
    recs = {}
    def rr(k):
        try: return k, store.bj(c, f"door/records/{k.split('/')[1]}/{store_index.slug(k.split('/', 2)[2])}.json")
        except Exception: return k, None
    with cf.ThreadPoolExecutor(32) as ex: recs = dict(ex.map(rr, list(by)))
    sector_of = {k: (((r or {}).get('identity') or {}).get('sector') or {}).get('value') for k, r in recs.items()}
    years = sorted(set(ys) | {datetime.date.today().year})
    out, tables = score_market(cc, by, sector_of, years)
    asof = datetime.date.today().isoformat(); n = 0
    if not dry:
        JS = ContentSettings(content_type='application/json')
        def put(item):
            k, s = item; doc = BF.sign({'cmr': k, 'as_of': asof, 'years_scored': years, 'years_note': f'{len(ys)} sealed year(s) plus the live window', **s,
                                        'method': 'cadence = results and statements per year; latency = days from the period end the filing states to its filing date (median, p90); silence = longest gap between dated lines; percentiles within the issuer\'s exchange and sector on this market (higher = more often / sooner / shorter silence)'})
            c.upload_blob(f"door/score/{k.split('/')[1]}/{store_index.slug(k.split('/', 2)[2])}.json", json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode(), overwrite=True, content_settings=JS)
        with cf.ThreadPoolExecutor(32) as ex: list(ex.map(put, out.items()))
        c.upload_blob('door/score/_tables.json', json.dumps(BF.sign({'node': node, 'as_of': asof, 'tables': tables}), ensure_ascii=False).encode(), overwrite=True, content_settings=JS)
    lat = sum(1 for s in out.values() if s['latency_days_median'] is not None)
    print(f"{node} score: {len(out)} issuers scored · years {years} · with latency {lat} · tables {len(tables)} · {'dry' if dry else 'written door/score/'}")
    json.dump({k: out[k] for k in list(out)[:50]}, open(os.path.join(os.environ.get('TEMP', '/tmp'), f'score-{cc}-sample.json'), 'w'), indent=1)
if __name__ == '__main__': sys.exit(main() or 0)
