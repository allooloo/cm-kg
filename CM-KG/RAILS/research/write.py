r"""write.py — USR-02 (2026-11-11): the research page, one per issuer, written from the numbers.
  join    the roll-up (rollup.py) + the orderability read (orderability.mjs) + the coverage and open-research read (coverage.py, newest drop) -> the page's
          numbers; numbers_hash = sha256 of the joined numbers (no clock value)
  write   one engine pass per issuer: Claude through the platform account, Haiku class (claude-haiku-5-5), writes the sentences of each section from the
          numbers, in the Allooloo register (flat declaratives; what it is, what it is not; the numbers as the sentence; no adjectives; no competitor named).
          Checked before it is kept: every figure in a sentence is a figure in the numbers; no word of view, rating or praise. A pass that fails the check
          twice is replaced by the template's own sentences (written by this rail from the same numbers) and marked so.
  write-on-change   a page is written on first read and rewritten only when numbers_hash changes; an unchanged issuer keeps its page byte for byte.
Sections, in order: the first-line fence; identity and listing; the disclosure read; auditor; events and halts; orderability; coverage; open research;
licensed (none loaded); as-of depth; sources.
Output: CM-KG\RESEARCH\pages\<cc>.jsonl (one page per line, sorted by cmr), <cc>.manifest.json, spend in CM-KG\RESEARCH\pages\<cc>.spend.json.
Usage: python -X utf8 write.py <cc> [...] [--threads N] [--limit N] [--no-engine]"""
import sys, os, re, json, glob, time, hashlib, threading, urllib.request, urllib.error, urllib.parse, concurrent.futures as cf
R = r'C:\ALLOOLOO\CM-KG\RESEARCH'; POND = r'C:\ALLOOLOO\CM-KG\POND'; MODEL = 'claude-haiku-5-5'
FENCE = "The page is the record's research on the issuer — no analyst, no rating, no view."
LICENSED = 'Licensed research: none loaded.'
SECTIONS = [('identity', 'Identity and listing'), ('disclosure', 'The disclosure read'), ('auditor', 'Auditor'), ('events', 'Events and halts'), ('orderability', 'Orderability'), ('coverage', 'Coverage'), ('open_research', 'Open research'), ('licensed', 'Licensed'), ('depth', 'As-of depth'), ('sources', 'Sources')]
WRITE = ['identity', 'disclosure', 'auditor', 'events', 'orderability', 'coverage', 'open_research', 'depth']
BANNED = re.compile(r'\b(strong|strongly|robust|impressive|leading|leader|significant|significantly|notable|notably|healthy|solid|weak|poor|concerning|excellent|good|bad|best|worst|attractive|bullish|bearish|outperform|underperform|recommend\w*|buy|sell|hold rating|outlook|promising|remarkable|substantial|well-positioned|high-quality|reliable|timely|diligent|transparent|unfortunately|importantly|interestingly|suggests?|indicat\w+|impl(y|ies)|likely|appears?|seems?)\b', re.I)
SP = {'calls': 0, 'input_tokens': 0, 'output_tokens': 0, 'cache_read': 0, 'cache_write': 0, 'retries': 0}; LOCK = threading.Lock(); KEY = None
SYSTEM = """You write one research page section set for Allooloo, from numbers taken off a signed public record. You are a writer of record, not an analyst.

The register:
- Flat declarative sentences. Present tense. Short.
- The number is the sentence: "The record holds 92 filings in the twelve months to 2026-11-08." Never round, never convert, never compute a new figure; use only figures that appear in the numbers given.
- Say what the record holds and, where the numbers say a field is not on the record, say so plainly with the record's own reason if one is given.
- No adjectives of quality or degree. No view, rating, recommendation, forecast, cause, interpretation or comparison judgement. "Above" and "below" a stated median are allowed as plain arithmetic facts; nothing more.
- No company other than the issuer, its auditor and the research houses in the numbers is named. No data vendor, no competitor.
- Do not mention Allooloo, the reader, or yourself. No headings, no lists, no markdown, no line breaks inside a section.
- Dates as YYYY-MM-DD. Write "not on the record" for a missing field.

Return JSON only, with exactly these keys, each a string of one to four sentences:
{"identity": "", "disclosure": "", "auditor": "", "events": "", "orderability": "", "coverage": "", "open_research": "", "depth": ""}

What each section states:
identity — the issuer's name, where it is listed, its ticker, ISIN and LEI, its security type, segment, sector and jurisdiction as the record holds them, and its listing status.
disclosure — filings in the window; filing days; the median gap between filing days (cadence); days from the latest filing to the record date (latency); the same medians for its exchange and for its sector on this market where given; the latest filing's date and type.
auditor — the auditor of record and its location; the auditor changes on the record, with dates; or that the market's record does not carry them.
events — the lifecycle lines on the record (listing, delisting, name change, domicile change, segment move) with dates, or that the index does not carry a type; and the halt flag.
orderability — the outcome per client category the market's chapter names (the signal code as given), or that the outcome is not determinable and why; the rule version.
coverage — how many research houses the issuer's own investor-relations page names and which, or that none was found on the pages read, or that the field has not been read.
open_research — how many openly published research notes are on the record, with publisher and date, or that none was found, or that the field has not been read.
depth — the sealed years that hold the issuer, the earliest sealed date of the market, when the live record began; or that the market's vintage is not sealed; or, where years are sealed in the store but not served as of a date, exactly that (the as-of door answers not_sealed)."""
def val(f): return f.get('value') if isinstance(f, dict) and 'value' in f else None
def nor(f): return 'not on the record' + (f" ({f['reason']})" if isinstance(f, dict) and f.get('reason') else '')
def latest(base):
    ds = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)) and re.match(r'^\d{4}-\d{2}-\d{2}', d)]; return os.path.join(base, sorted(ds, key=lambda d: (d[:10], int(d[11:] or 1)))[-1]) if ds else None
def join(cc):
    rows = [json.loads(l) for l in open(os.path.join(R, 'numbers', f'{cc}.jsonl'), encoding='utf-8')]
    op = os.path.join(R, 'orderability', f'{cc}.json'); O = json.load(open(op, encoding='utf-8')) if os.path.exists(op) else None
    cb = os.path.join(POND, f'{cc}-cm-kg', 'research-coverage'); cd = latest(cb) if os.path.isdir(cb) else None; C = {}
    if cd and os.path.exists(os.path.join(cd, 'raw.jsonl')):
        for l in open(os.path.join(cd, 'raw.jsonl'), encoding='utf-8'): j = json.loads(l); C[j['cmr']] = j
    for o in rows:
        o.pop('numbers_hash', None)
        if O is None: o['orderability'] = {'state': 'not_read', 'note': 'the orderability outcome has not been read for this market'}
        elif O.get('node_outcome'): n = O['node_outcome']; o['orderability'] = {'determinable': False, 'client_categories': [], 'reason': (n['blocking_gaps'][0]['reason'] if n.get('blocking_gaps') else n.get('note')), 'rule_version': n.get('rule_version'), 'chapter_as_of': n.get('chapter_as_of'), 'section': n.get('section'), 'read': {'tool': 'get_orderability', 'door': O['door'], 'chapter': O['chapter_file']}}
        else:
            g = O['groups'].get(O['of'].get(o['cmr']) or '', {}); any1 = next(iter(g.values()), {})
            o['orderability'] = {'client_categories': O['client_categories'], 'outcomes': {c: {'signal': x.get('signal'), 'determinable': x.get('determinable'), **({'reason': x['blocking_gaps'][0]['reason']} if not x.get('signal') and x.get('blocking_gaps') else {})} for c, x in sorted(g.items())}, 'rule_version': any1.get('rule_version'), 'chapter_as_of': any1.get('chapter_as_of'), 'section': any1.get('section'), 'read': {'tool': 'get_orderability', 'door': O['door'], 'chapter': O['chapter_file'], 'basis': 'one live read per instrument class, halt state and client category on this market; this issuer\'s group'}}
        c = C.get(o['cmr'])
        if c: o['coverage'] = {**c['coverage'], 'pages_checked': [p for p in c.get('pages_checked', [])], 'read_by': c.get('engine')}; o['open_research'] = c['open_research']
        o['numbers_hash'] = 'sha256:' + hashlib.sha256(json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return rows
def digest(o):
    """the numbers the writer is given: values only, compact"""
    i = o['identity']; d = o['disclosure']; a = o['auditor']; lc = o['lifecycle']; od = o['orderability']; cv = o['coverage']; orr = o['open_research']; dp = o['as_of_depth']
    f = lambda x: val(x) if val(x) is not None else nor(x)
    return {'record_date': o['record']['as_of'], 'market': o['market'],
        'identity': {k: f(i[k]) for k in ('name', 'exchange', 'ticker', 'isin', 'lei', 'security_type', 'segment', 'sector', 'jurisdiction')} | {'status': o['status']['value'], **({'halted_since': o['status']['since']} if o['status'].get('since') else {})},
        'disclosure': {'window_from': d['window']['from'], 'window_to': d['window']['to'], 'filings': d['filings'], 'filing_days': d['filing_days'], 'by_type': d['by_type'], 'median_gap_days_between_filing_days': d['cadence_median_gap_days'], 'latest_filing_date': d['latest_filing_date'], 'days_from_latest_filing_to_record_date': d['latency_days'], 'latest_filing_type': (d['latest'][0]['type'] if d['latest'] else None), 'exchange_peers': d['against']['exchange'], 'sector_peers': d['against']['sector']},
        'auditor': {'auditor': f(a['auditor']), 'location': f(a['auditor_location']), 'changes': [c['date'] for c in a['changes']] if isinstance(a['changes'], list) else nor(a['changes'])},
        'events': {t: ([x['date'] for x in v] if isinstance(v, list) else nor(v)) for t, v in lc.items()} | {'halt': o['status']['value']},
        'orderability': {k: od[k] for k in od if k not in ('read', 'section')},
        'coverage': {'state': cv['state'], **({'houses': [h['house'] for h in cv.get('houses', [])], 'count': cv.get('count')} if cv['state'] != 'not_read' else {})},
        'open_research': {'state': orr['state'], 'notes': [{'publisher': r['publisher'], 'date': r['date']} for r in orr.get('rows', [])]},
        'depth': {'vintage_sealed': dp['sealed'], 'issuer_years_sealed': dp['issuer_years_sealed'], 'market_earliest_sealed_date': dp['node_history_from'], 'live_record_began': dp['live_record_began'], **({'years_sealed_in_the_store_but_not_served_as_of_a_date': dp['store_years_sealed_not_served'], 'as_of_door_answer': 'not_sealed'} if dp.get('store_years_sealed_not_served') else {})}}
def template(o):
    """the template's own sentences, from the same numbers — used when the engine pass fails its check, and with --no-engine"""
    g = digest(o); i = g['identity']; d = g['disclosure']; a = g['auditor']; e = g['events']; od = o['orderability']; cv = o['coverage']; orr = o['open_research']; dp = g['depth']; s = {}
    s['identity'] = f"{i['name']} is listed on {i['exchange']} under the ticker {i['ticker']}. ISIN: {i['isin']}. LEI: {i['lei']}. Security type: {i['security_type']}; segment: {i['segment']}; sector: {i['sector']}; jurisdiction: {i['jurisdiction']}. Status: {i['status']}."
    if d['filings']:
        pe = d['exchange_peers']; ps = d['sector_peers']; x = f"The record holds {d['filings']} filings on {d['filing_days']} filing days from {d['window_from']} to {d['window_to']}."
        if d['median_gap_days_between_filing_days'] is not None: x += f" The median gap between filing days is {d['median_gap_days_between_filing_days']} days."
        x += f" The latest filing is dated {d['latest_filing_date']}, {d['days_from_latest_filing_to_record_date']} days before the record date."
        if pe.get('median_filings') is not None: x += f" On {pe['name']} ({pe['issuers']} issuers) the median is {pe['median_filings']} filings, a gap of {pe['median_cadence_gap_days']} days and a latency of {pe['median_latency_days']} days."
        if ps.get('median_filings') is not None: x += f" In sector {ps['name']} ({ps['issuers']} issuers) the median is {ps['median_filings']} filings, a gap of {ps['median_cadence_gap_days']} days and a latency of {ps['median_latency_days']} days."
        s['disclosure'] = x
    else: s['disclosure'] = f"The record holds no filing for this issuer from {d['window_from']} to {d['window_to']}."
    s['auditor'] = f"Auditor of record: {a['auditor']}. Location: {a['location']}. " + (f"Auditor changes on the record: {len(a['changes'])}" + (f" ({', '.join(a['changes'])})." if a['changes'] else '.') if isinstance(a['changes'], list) else f"Auditor changes: {a['changes']}.")
    s['events'] = ' '.join(f"{t.replace('_', ' ').capitalize()}: {(str(len(v)) + (' (' + ', '.join(x or 'undated' for x in v) + ')' if v else '')) if isinstance(v, list) else v}." for t, v in e.items() if t != 'halt') + f" Halt flag: {e['halt']}."
    if od.get('state') == 'not_read': s['orderability'] = 'The orderability outcome has not been read for this market.'
    elif od.get('outcomes'): s['orderability'] = ' '.join(f"Client category {c}: {x['signal'] or 'not determinable'}." for c, x in od['outcomes'].items()) + f" Rule version: {od.get('rule_version')}."
    else: s['orderability'] = f"The orderability outcome is not determinable: {od.get('reason')}. Rule version: {od.get('rule_version')}."
    s['coverage'] = 'The coverage field has not been read for this issuer.' if cv['state'] == 'not_read' else f"The issuer's investor-relations page names {cv['count']} research houses: {', '.join(h['house'] for h in cv['houses'])}." if cv['state'] == 'found' else 'No research house was found on the pages read.'
    s['open_research'] = 'The open-research field has not been read for this issuer.' if orr['state'] == 'not_read' else f"The record holds {len(orr['rows'])} openly published research notes: " + '; '.join(f"{r['publisher']}" + (f" ({r['date']})" if r['date'] else '') for r in orr['rows']) + '.' if orr.get('rows') else 'No openly published research note was found.'
    s['depth'] = (f"Sealed years holding this issuer: {', '.join(dp['issuer_years_sealed']) or 'none'}. The market's earliest sealed date is {dp['market_earliest_sealed_date']}. The live record began {dp['live_record_began']}." if dp['vintage_sealed'] else f"Years sealed in the {o['market']} store: {', '.join(dp['years_sealed_in_the_store_but_not_served_as_of_a_date'])}. Their Replay split is not built; the as-of door answers not_sealed. The record is the live record as of {o['record']['as_of']}." if dp.get('years_sealed_in_the_store_but_not_served_as_of_a_date') else f"The {o['market']} vintage is not sealed. The record is the live record as of {o['record']['as_of']}.")
    return s
NUMRE = re.compile(r'\d+(?:[.,]\d+)*')
def check(text, g):
    hay = json.dumps(g, ensure_ascii=False); bad = [n for n in NUMRE.findall(text) if n.rstrip('.,') not in hay and n.replace(',', '') not in hay]
    if bad: return 'figure not in the numbers: ' + ', '.join(bad[:4])
    low = hay.lower(); m = next((x for x in BANNED.finditer(text) if x.group(0).lower() not in low), None)   # a word the record itself carries (an issuer's name, a field's own reason) is the record's, not a view
    return f'word of view: {m.group(0)}' if m else None
def engine(o):
    g = digest(o); body = {'model': MODEL, 'max_tokens': 1400, 'thinking': {'type': 'disabled'}, 'system': [{'type': 'text', 'text': SYSTEM, 'cache_control': {'type': 'ephemeral'}}], 'messages': [{'role': 'user', 'content': 'The numbers:\n' + json.dumps(g, ensure_ascii=False)}]}
    why = None
    for attempt in range(2):
        j = None
        for i in range(6):
            try: j = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.anthropic.com/v1/messages', data=json.dumps(body).encode(), headers={'x-api-key': KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}), timeout=120).read()); break
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 529): time.sleep(5 * (i + 1)); continue
                why = f'engine {e.code}'; break
            except Exception as e: time.sleep(3 * (i + 1)); why = type(e).__name__
        if not j: break
        u = j.get('usage') or {}
        with LOCK: SP['calls'] += 1; SP['input_tokens'] += u.get('input_tokens', 0); SP['output_tokens'] += u.get('output_tokens', 0); SP['cache_read'] += u.get('cache_read_input_tokens', 0); SP['cache_write'] += u.get('cache_creation_input_tokens', 0)
        try: m = re.search(r'\{.*\}', ''.join(b.get('text', '') for b in j['content'] if b.get('type') == 'text'), re.S); s = json.loads(m.group(0))
        except Exception: why = 'not JSON'; s = None
        if s and all(isinstance(s.get(k), str) and s[k].strip() for k in WRITE):
            why = next((f'{k}: {w}' for k in WRITE if (w := check(s[k], g))), None)
            if not why: return {k: re.sub(r'\s+', ' ', s[k]).strip() for k in WRITE}, None
        elif s: why = 'a section is missing'
        with LOCK: SP['retries'] += 1
        body['messages'] = [{'role': 'user', 'content': 'The numbers:\n' + json.dumps(g, ensure_ascii=False) + f'\n\nA first pass was refused ({why}). Use only figures present in the numbers and no word of view.'}]
    return None, why or 'engine did not answer'
def sources(o):
    seen = []; add = lambda u, w: (u and str(u).startswith('http') and not any(x['source'] == u for x in seen)) and seen.append({'source': u, 'for': w})
    for k, f in o['identity'].items(): add(isinstance(f, dict) and f.get('source') and str(f['source']).split(' ')[0], f'identity.{k}')
    add(o['disclosure'].get('source'), 'the disclosure lines'); add(o['status'].get('source'), 'the halt flag'); add(o['auditor']['auditor'].get('source'), 'the auditor')
    od = o['orderability'].get('read') or {}; add(od.get('chapter'), 'the orderability chapter')
    for h in o['coverage'].get('houses', []): add(h['source'], 'coverage')
    for r in o['open_research'].get('rows', []): add(r['source'], 'open research')
    add(o['record'].get('url'), 'the record'); return seen
def page(o, sent, writer):
    cc = o['market'].lower(); _, ex, code = o['cmr'].split('/', 2); name = val(o['identity']['name']) or code; tick = val(o['identity']['ticker']) or code
    path = f"/{cc}/{urllib.parse.quote(ex, safe='')}/{urllib.parse.quote(code, safe='')}"; sent = dict(sent); sent['licensed'] = LICENSED + ' ' + o['licensed']['rule']; src = sources(o)
    sent['sources'] = f"{len(src)} source pages are named on this page; every value above carries its own source page and read date in the numbers."
    secs = [{'id': k, 'title': t, 'text': sent[k]} for k, t in SECTIONS]
    md = f"{FENCE}\n\n# {name} ({val(o['identity']['exchange']) or ex}: {tick}) — research page\n\nAs of {o['record']['as_of']} · {o['node']} · record version {o['record']['version']}\n\n" + '\n\n'.join(f"## {s['title']}\n\n{s['text']}" for s in secs) + '\n\n' + '\n'.join(f"- {x['source']} ({x['for']})" for x in src) + '\n'
    return {'schema': 'research-page v0.1 (USR-02, 2026-11-11)', 'cmr': o['cmr'], 'node': o['node'], 'market': o['market'], 'path': path, 'title': f"{name} ({tick}) — research page", 'fence': FENCE, 'as_of': o['record']['as_of'], 'numbers_hash': o['numbers_hash'], 'writer': writer, 'sections': secs, 'sources': src, 'markdown': md, 'numbers': o}
def build(cc, threads, limit, no_engine):
    rows = join(cc); pd = os.path.join(R, 'pages'); os.makedirs(pd, exist_ok=True); pf = os.path.join(pd, f'{cc}.jsonl'); old = {}
    if os.path.exists(pf):
        for l in open(pf, encoding='utf-8'): j = json.loads(l); old[j['cmr']] = j
    keep = {o['cmr']: old[o['cmr']] for o in rows if o['cmr'] in old and old[o['cmr']]['numbers_hash'] == o['numbers_hash'] and (no_engine or old[o['cmr']]['writer']['engine'] or not re.search(r'refused: (engine \d+|engine did not answer|\w+Error)', old[o['cmr']]['writer']['by']))}   # write-on-change: a page stands until its numbers change (the engine's two tries are inside one run); only a page whose engine did not answer at all is tried again
    if os.path.exists(pf + '.part'):   # a run that was cut short: its written pages are kept where the numbers still match
        H = {o['cmr']: o['numbers_hash'] for o in rows}
        for l in open(pf + '.part', encoding='utf-8'):
            try: j = json.loads(l)
            except Exception: continue
            if H.get(j['cmr']) == j['numbers_hash'] and j['writer']['engine']: keep[j['cmr']] = j
    todo = [o for o in rows if o['cmr'] not in keep]
    if limit: todo = todo[:limit]
    print(cc, 'issuers', len(rows), 'unchanged (kept)', len(keep), 'to write', len(todo), flush=True); new = {}; fb = [0]; n = [0]
    def one(o):
        if no_engine: return page(o, template(o), {'engine': None, 'by': 'the template\'s own sentences (no engine pass)'})
        s, why = engine(o)
        if s: return page(o, s, {'engine': MODEL, 'by': 'Claude through the platform account, Haiku class; one pass; checked against the numbers'})
        with LOCK: fb[0] += 1
        return page(o, template(o), {'engine': None, 'by': f'the template\'s own sentences (the engine pass was refused: {why})', 'tries': (old.get(o['cmr'], {}).get('writer', {}).get('tries', 0) if old.get(o['cmr'], {}).get('numbers_hash') == o['numbers_hash'] else 0) + 1})
    with cf.ThreadPoolExecutor(threads) as ex:
        for p in ex.map(one, todo):
            new[p['cmr']] = p; n[0] += 1
            if n[0] % 500 == 0:
                print(cc, n[0], '/', len(todo), 'template fallbacks', fb[0], json.dumps(SP), flush=True)
                with open(pf + '.part', 'w', encoding='utf-8') as f:
                    for c in sorted({**keep, **new}): f.write(json.dumps({**keep, **new}[c], ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
    allp = {**{c: p for c, p in old.items() if limit and c not in new and c not in keep and any(o['cmr'] == c for o in rows)}, **keep, **new}
    body = ''.join(json.dumps(allp[c], ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for c in sorted(allp)).encode()
    if os.path.exists(pf) and new: os.replace(pf, pf.replace('.jsonl', f'.pre-{time.strftime("%Y%m%dT%H%M%S")}.jsonl'))
    open(pf, 'wb').write(body)
    if os.path.exists(pf + '.part'): os.remove(pf + '.part')
    cov = [p['numbers']['coverage']['state'] for p in allp.values()]; man = {'node': f'{cc}-cm-kg', 'pages': len(allp), 'written_this_run': len(new), 'kept_unchanged': len(keep), 'by_engine': sum(1 for p in allp.values() if p['writer']['engine']), 'by_template': sum(1 for p in allp.values() if not p['writer']['engine']),
        'coverage_found': cov.count('found'), 'coverage_none_found': cov.count('none_found'), 'coverage_not_read': cov.count('not_read'), 'open_research_rows': sum(len(p['numbers']['open_research'].get('rows', [])) for p in allp.values()), 'licensed_rows': sum(len(p['numbers']['licensed']['rows']) for p in allp.values()), 'record_as_of': max(p['as_of'] for p in allp.values()), 'sha256': hashlib.sha256(body).hexdigest()}
    json.dump(man, open(os.path.join(pd, f'{cc}.manifest.json'), 'w'), indent=1); sp = os.path.join(pd, f'{cc}.spend.json'); prev = json.load(open(sp)) if os.path.exists(sp) else {}
    json.dump({k: prev.get(k, 0) + v for k, v in SP.items()}, open(sp, 'w'), indent=1); print(json.dumps(man), json.dumps(SP), flush=True)
    for k in SP: SP[k] = 0
if __name__ == '__main__':
    a = sys.argv[1:]; th = int(a[a.index('--threads') + 1]) if '--threads' in a else 16; lim = int(a[a.index('--limit') + 1]) if '--limit' in a else None; ne = '--no-engine' in a
    if not ne: KEY = open(r'C:\ALLOOLOO\AGENT KEYS\claude.txt', encoding='utf-8').read().strip().splitlines()[0]
    ccs = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] not in ('--threads', '--limit'))]; bad = 0
    for cc in ccs:
        try: build(cc, th, lim, ne)
        except Exception as e: bad += 1; import traceback; traceback.print_exc(); print(cc, 'FAILED', repr(e)[:300], flush=True)
    sys.exit(1 if bad else 0)
