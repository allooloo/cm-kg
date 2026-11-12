r"""exchange.py — USR-04 (2026-11-12): the exchange page, one per venue on the roster, built from the issuer pages it lists (CM-KG\RESEARCH\pages\<cc>.jsonl).
The venue read as a whole, on the issuer page's template: the fence; identity (venue, node, regulator, halts page, disclosure channel — the venue roster);
the disclosure read (medians over its issuers); auditors; events and halts; orderability; coverage; open research; licensed (none loaded); as-of depth;
sources; then every listed company on the venue with a research page. Sentences are the template's own, from the numbers: no engine, no clock value, so two
builds are identical. Writes CM-KG\RESEARCH\exchanges\<cc>.json and, with --publish, the page store (x:<cc>/<EX>, and xi:<cc> the market's venue list).
Usage: python -X utf8 exchange.py [--publish] <cc> [...]"""
import sys, os, json, time, statistics, collections, hashlib, urllib.request, urllib.error, urllib.parse
R = r'C:\ALLOOLOO\CM-KG\RESEARCH'; A = 'dd2832b36f171b815f84c8487aada36b'; NS = '7d0e0e4a059e444982b5eb1cc500efc1'
FENCE = "The page is the record's research on the issuer — no analyst, no rating, no view."; VEN = json.load(open(os.path.join(R, 'venues.json'), encoding='utf-8'))
med = lambda xs: (lambda v: round(statistics.median(v), 1) if v else None)([x for x in xs if x is not None])
def fv(f): return f.get('value') if isinstance(f, dict) and 'value' in f else None
def build(cc):
    pages = [json.loads(l) for l in open(os.path.join(R, 'pages', f'{cc}.jsonl'), encoding='utf-8')]; by = collections.defaultdict(list); bn = VEN['by_node'].get(cc, {})
    for p in pages: by[p['cmr'].split('/', 2)[1]].append(p)
    out = []
    for ex in sorted(by):
        ps = sorted(by[ex], key=lambda p: (str(fv(p['numbers']['identity']['name']) or '').lower(), p['cmr'])); N = [p['numbers'] for p in ps]; n = len(ps)
        name = collections.Counter(fv(x['identity']['exchange']) or ex for x in N).most_common(1)[0][0]; as_of = max(p['as_of'] for p in ps); D = [x['disclosure'] for x in N]
        aud = collections.Counter(fv(x['auditor']['auditor']) for x in N if fv(x['auditor']['auditor'])); halted = sum(1 for x in N if x['status']['value'] == 'halted')
        sig = collections.Counter(); cats = []
        for x in N:
            od = x.get('orderability') or {}
            if od.get('outcomes'):
                cats = cats or list(od['outcomes'])
                for c, o in od['outcomes'].items(): sig[(c, o.get('signal') or 'not determinable')] += 1
            else: sig[('—', 'not determinable')] += 1
        cov = [x['coverage'] for x in N]; found = sum(1 for c in cov if c['state'] == 'found'); none = sum(1 for c in cov if c['state'] == 'none_found'); notread = sum(1 for c in cov if c['state'] == 'not_read')
        houses = collections.Counter(h['house'] for c in cov for h in c.get('houses', [])); notes = sum(len(x['open_research'].get('rows', [])) for x in N); wn = sum(1 for x in N if x['open_research'].get('rows'))
        sealed = sum(1 for x in N if x['as_of_depth']['issuer_years_sealed']); dp = N[0]['as_of_depth']; lc = collections.Counter()
        for x in N:
            for t, v in x['lifecycle'].items():
                if isinstance(v, list): lc[t] += len(v)
        stats = {'issuers': n, 'filings_total': sum(d['filings'] for d in D), 'median_filings': med([d['filings'] for d in D]), 'median_cadence_gap_days': med([d['cadence_median_gap_days'] for d in D]), 'median_latency_days': med([d['latency_days'] for d in D]), 'issuers_with_no_filing': sum(1 for d in D if not d['filings']),
                 'auditor_named': sum(aud.values()), 'auditors': aud.most_common(10), 'halted': halted, 'lifecycle_lines': dict(sorted(lc.items())), 'orderability': [[c, s, k] for (c, s), k in sorted(sig.items())],
                 'coverage_found': found, 'coverage_none_found': none, 'coverage_not_read': notread, 'houses_most_named': houses.most_common(10), 'open_research_rows': notes, 'issuers_with_open_research': wn, 'issuers_in_a_sealed_year': sealed}
        f = lambda b: (b.get('value') if isinstance(b, dict) and b.get('value') else 'not on the market file')
        S = collections.OrderedDict()
        S['identity'] = ('Identity and listing', f"{name} ({ex}) is a venue of the {bn.get('country', cc.upper())} market, held on node {cc}-cm-kg. Regulator: {f(bn.get('regulator'))}. Halts page: {f(bn.get('halts_page'))}. Disclosure channel: {f(bn.get('disclosure_channel'))}.")
        S['disclosure'] = ('The disclosure read', f"{n} listed companies on {name} have a research page. Their records hold {stats['filings_total']} filings in the trailing twelve months. The median issuer holds {stats['median_filings']} filings, with a median gap of {stats['median_cadence_gap_days']} days between filing days and {stats['median_latency_days']} days from the latest filing to the record date. {stats['issuers_with_no_filing']} issuers hold no filing in the window.")
        S['auditor'] = ('Auditor', (f"The record names an auditor for {stats['auditor_named']} of the {n} issuers. Most named: " + '; '.join(f'{a} ({k})' for a, k in aud.most_common(5)) + '.') if aud else f"The record names no auditor for the issuers of {name}.")
        S['events'] = ('Events and halts', f"Halted on the record date: {halted} of {n}. Lifecycle lines on the record: " + ('; '.join(f"{t.replace('_', ' ')} {k}" for t, k in sorted(lc.items())) if lc else 'none') + '.')
        S['orderability'] = ('Orderability', ' '.join(f"Client category {c}: {s} for {k} issuers." if c != '—' else f"Not determinable for {k} issuers: the market's chapter names no client category." for (c, s), k in sorted(sig.items())))
        S['coverage'] = ('Coverage', f"Coverage found on {found} issuer pages, none found on {none}, not read on {notread}." + (' Houses most named: ' + '; '.join(f'{h} ({k})' for h, k in houses.most_common(5)) + '.' if houses else ''))
        S['open_research'] = ('Open research', f"{notes} openly published research notes are on the record, across {wn} issuers.")
        S['licensed'] = ('Licensed', 'Licensed research: none loaded. A licensed row is served only to an agent whose firm holds that licence (licensor, entitlement). No licensed row is loaded.')
        S['depth'] = ('As-of depth', (f"{sealed} of the {n} issuers are held in a sealed year. The market's earliest sealed date is {dp['node_history_from']}." if dp['sealed'] else dp.get('note') or 'The vintage is not sealed.'))
        srcs = [{'source': s, 'for': w} for s, w in ((str((bn.get(k) or {}).get('source') or '').split(' ')[0], w) for k, w in (('regulator', 'the regulator'), ('halts_page', 'the halts page'), ('disclosure_channel', 'the disclosure channel'))) if s.startswith('http')] + [{'source': f'https://getresearch.ai/{cc}', 'for': 'the issuer pages this page is built from'}]
        S['sources'] = ('Sources', f"This page is built from the {n} issuer pages it lists; each carries its own sources. {len(srcs)} pages are named here.")
        path = f"/{cc}/{urllib.parse.quote(ex, safe='')}"
        o = {'schema': 'research-exchange-page v0.1 (USR-04, 2026-11-12)', 'kind': 'exchange', 'exchange': ex, 'name': name, 'node': f'{cc}-cm-kg', 'market': cc.upper(), 'country': bn.get('country'), 'path': path, 'as_of': as_of, 'fence': FENCE, 'title': f'{name} — listed companies on the record', 'stats': stats,
             'sections': [{'id': k, 'title': t, 'text': x} for k, (t, x) in S.items()], 'sources': srcs, 'venue': {k: bn.get(k) for k in ('regulator', 'halts_page', 'disclosure_channel')},
             'issuers': [[p['cmr'].split('/', 2)[2], fv(p['numbers']['identity']['name']), fv(p['numbers']['identity']['ticker']), fv(p['numbers']['identity']['isin'])] for p in ps]}
        o['markdown'] = f"{FENCE}\n\n# {o['title']}\n\nAs of {as_of} · {cc}-cm-kg · {ex}\n\n" + '\n\n'.join(f"## {t}\n\n{x}" for t, x in S.values()) + '\n\n' + '\n'.join(f"- {s['source']} ({s['for']})" for s in srcs) + '\n\n## Listed companies\n\n' + '\n'.join(f"- [{i[1] or i[0]}](https://getresearch.ai{path}/{urllib.parse.quote(i[0], safe='')})" for i in o['issuers']) + '\n'
        o['page_hash'] = 'sha256:' + hashlib.sha256(json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest(); out.append(o)
    os.makedirs(os.path.join(R, 'exchanges'), exist_ok=True); body = json.dumps(out, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode(); open(os.path.join(R, 'exchanges', f'{cc}.json'), 'wb').write(body)
    return out, hashlib.sha256(body).hexdigest()
def put(pairs):
    TOK = os.environ.get('CLOUDFLARE_KV_TOKEN') or open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0]; b = json.dumps([{'key': k, 'value': json.dumps(v, ensure_ascii=False, separators=(',', ':'))} for k, v in pairs]).encode()
    for i in range(6):
        try:
            r = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://api.cloudflare.com/client/v4/accounts/{A}/storage/kv/namespaces/{NS}/bulk', method='PUT', data=b, headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json'}), timeout=180).read())
            if r.get('success'): return
            raise RuntimeError(json.dumps(r.get('errors'))[:200])
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 520, 524): time.sleep(8 * (i + 1)); continue
            raise RuntimeError(f'{e.code} {e.read()[:200]!r}')
    raise RuntimeError('retries')
a = sys.argv[1:]; pub = '--publish' in a; tot = 0; bad = 0
for cc in [x for x in a if not x.startswith('--')]:
    try:
        out, sha = build(cc); tot += len(out)
        if pub: put([(f"x:{cc}/{o['exchange']}", o) for o in out] + [(f'xi:{cc}', [[o['exchange'], o['name'], o['stats']['issuers']] for o in out])])
        print(cc, 'exchange pages', len(out), [(o['exchange'], o['stats']['issuers']) for o in out], sha[:12], 'published' if pub else '', flush=True)
    except Exception as e: bad += 1; import traceback; traceback.print_exc(); print(cc, 'FAILED', repr(e)[:200], flush=True)
print('exchange pages', tot); sys.exit(1 if bad else 0)
