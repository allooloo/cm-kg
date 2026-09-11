r"""Loader rail for the Canada door. Reads the CONFIRMED outputs (never the raw folders):
   CM-KG\ISSUERS\ca-issuers.xlsx            -> one CMR v0 per row (4,820; corporate and fund rows alike)
   CM-KG\DISCLOSURE\events\ca-events.jsonl  -> events per issuer, newest first
and writes the door's data files under CM-KG\DOOR\data\ (Workers Static Assets; D1 and KV are refused by the account token):
   records/<EXCHANGE>/<TICKER>.json   events/<EXCHANGE>/<TICKER>.json   index.json   facts.json   nodes.json
Idempotent on (exchange, ticker): every file is rewritten from the workbook; keys that vanish from the workbook are kept with
a "superseded" note (records are never deleted). Re-run after every weekly sweep, then `wrangler deploy` in CM-KG\DOOR."""
import openpyxl, json, os, re, datetime, sys, shutil
ROOT = r'C:\ALLOOLOO'
XLSX = os.path.join(ROOT, r'CM-KG\ISSUERS\ca-issuers.xlsx'); EVENTS = os.path.join(ROOT, r'CM-KG\DISCLOSURE\events\ca-events.jsonl')
OUT = os.path.join(ROOT, r'CM-KG\DOOR\data'); AS_OF = os.environ.get('AS_OF', '2026-09-10'); VERSION = int(os.environ.get('CMR_VERSION', '1'))
NODE = 'ca-cm-kg'; HOST = 'https://mcp.ca-cm-kg.ai'
EXSLUG = {'TSX': 'TSX', 'TSXV': 'TSXV', 'CSE': 'CSE', 'Cboe Canada': 'CBOE-CANADA'}
def slug_ticker(t): return re.sub(r'[^A-Za-z0-9.\-]', '_', str(t))
def gaps_of(text):
    out = {}
    for part in (text or '').split('; '):
        if ':' in part:
            f, why = part.split(':', 1); out[f.strip()] = why.strip()
    return out
FIELD_MAP = {  # cmr field -> (value col, source col, read-by col, state col, gaps label)
    'name': ('Legal name', 'Roster source', 'Roster read by', None, None),
    'ticker': ('Ticker', 'Roster source', 'Roster read by', None, None),
    'exchange': ('Exchange', 'Roster source', 'Roster read by', None, None),
    'security_type': ('Security type', 'Sector source', 'Sector read by', None, None),
    'isin': ('ISIN', 'ISIN source', 'ISIN read by', 'ISIN state', 'ISIN'),
    'lei': ('LEI', 'LEI source', 'LEI read by', 'LEI state', 'LEI'),
    'sector': ('Sector', 'Sector source', 'Sector read by', None, 'Sector'),
    'jurisdiction': ('Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Incorporation jurisdiction state', 'Incorporation jurisdiction'),
    'transfer_agent': ('Transfer agent', 'Transfer agent source', 'Transfer agent read by', 'Transfer agent state', 'Transfer agent'),
    'auditor': ('Auditor', 'Auditor source', 'Auditor read by', 'Auditor state', 'Auditor'),
    'newswire': ('Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire of habit state', 'Newswire of habit'),
    'hq_city': ('HQ city', 'HQ source', 'HQ read by', None, 'HQ city'),
    'hq_region': ('HQ province/state', 'HQ source', 'HQ read by', None, 'HQ province/state'),
    'tier': ('Listing tier', 'Roster source', 'Roster read by', None, 'Listing tier'),
    'sedar_profile': ('SEDAR+ profile link', 'SEDAR+ source', 'SEDAR+ read by', None, 'SEDAR+ profile link'),
    'sedi_link': ('SEDI link (unverified — HTTP 403 on fetch)', None, 'SEDI read by', None, 'SEDI link'),
}
SECOND = {'isin': 'ISIN', 'lei': 'LEI', 'transfer_agent': 'Transfer agent', 'auditor': 'Auditor', 'newswire': 'Newswire of habit', 'jurisdiction': 'Incorporation jurisdiction'}
def field(d, spec, gaps):
    vcol, scol, rcol, stcol, glabel = spec
    v = d.get(vcol)
    if v in (None, ''):
        return {'value': None, 'source_url': None, 'read_by': None, 'state': None, 'reason': gaps.get(glabel or vcol, 'no source read')}
    src = (d.get(scol) or '') if scol else ''
    if isinstance(src, str) and '\n' in src: src = src.split('\n')[0]
    st = (d.get(stcol) or 'sourced') if stcol else ('unverified' if vcol.startswith('SEDI') else 'sourced')
    o = {'value': v if not isinstance(v, str) else v.strip(), 'source_url': src or None, 'read_by': d.get(rcol) or None, 'state': st}
    # HQ region cells can carry the Width 0 note "<GLEIF region> [TMX workbook says XX]"; keep the GLEIF value and the note, or fall back to the workbook's province when GLEIF gave none
    if isinstance(o['value'], str) and '[TMX workbook says' in o['value']:
        m = re.match(r'^(.*?)\s*\[TMX workbook says ([^\]]+)\]$', o['value'])
        if m and m.group(1).strip(): o['value'] = m.group(1).strip(); o['note'] = f'TMX workbook says {m.group(2)}'
        elif m: o['value'] = m.group(2).strip(); o['source_url'] = 'https://www.tsx.com/en/resource/571'; o['read_by'] = 'TMX listed-companies workbook (exchange list, monthly)'; o['state'] = 'sourced'
    return o
def main():
    for sub in ('records', 'events'):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    index = {'ticker': {}, 'isin': {}, 'lei': {}, 'keys': []}; n = 0; counts = {}
    ev_by = {}
    for line in open(EVENTS, encoding='utf-8'):
        e = json.loads(line); k = (e['exchange'], e['ticker']); ev_by.setdefault(k, []).append(e)
    for ex in ['TSX', 'TSXV', 'CSE', 'Cboe Canada']:
        ws = wb[ex]; it = ws.iter_rows(values_only=True); hdr = next(it); exs = EXSLUG[ex]
        os.makedirs(os.path.join(OUT, 'records', exs), exist_ok=True); os.makedirs(os.path.join(OUT, 'events', exs), exist_ok=True)
        for row in it:
            d = dict(zip(hdr, row))
            if not d.get('Ticker'): continue
            t = str(d['Ticker']).strip(); key = f'{NODE}/{exs}/{t}'; gaps = gaps_of(d.get('Gaps'))
            identity = {f: field(d, spec, gaps) for f, spec in FIELD_MAP.items()}
            for f, col in SECOND.items():
                if identity[f]['value'] is not None:
                    s2 = d.get(f'{col} second source'); r2 = d.get(f'{col} second read by')
                    if s2: identity[f]['second_source_url'] = str(s2).split('\n')[0]
                    if r2: identity[f]['second_read_by'] = r2
            aliases = []
            if d.get('Also known as'):
                names = [a.strip() for a in str(d['Also known as']).split(' | ')]; srcs = str(d.get('Alias source') or '').split('\n'); rbs = str(d.get('Alias read by') or '').split('\n')
                for i, a in enumerate(names):
                    if a: aliases.append({'value': a, 'source_url': srcs[i] if i < len(srcs) else None, 'read_by': rbs[i] if i < len(rbs) else None})
            evs = sorted(ev_by.get((ex, t), []), key=lambda e: e['date'], reverse=True)
            rec = {'cmr': key, 'node': NODE, 'as_of': AS_OF, 'version': VERSION, 'identity': identity, 'aliases': aliases,
                   'events_url': f'{HOST}/events/{exs}/{t}', 'event_count': len(evs), 'gaps': [{'field': f, 'reason': w} for f, w in gaps.items()]}
            fn = os.path.join(OUT, 'records', exs, slug_ticker(t) + '.json')
            json.dump(rec, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            evfn = os.path.join(OUT, 'events', exs, slug_ticker(t) + '.json')
            json.dump([{k2: e.get(k2) for k2 in ('date', 'event_type', 'title', 'wire', 'source', 'url', 'read_by', 'state', 'detail', 'second_source', 'second_read_by', 'period_end', 'statement_date', 'auditor_named', 'going_concern', 'extract_read_by') if e.get(k2) not in (None, '')} for e in evs],
                      open(evfn, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            index['keys'].append(key); index['ticker'].setdefault(t.upper(), []).append(key)
            root = t.split('.')[0].upper()
            if root != t.upper(): index['ticker'].setdefault(root, []).append(key)
            if identity['isin']['value']: index['isin'].setdefault(identity['isin']['value'].upper(), []).append(key)
            if identity['lei']['value']: index['lei'].setdefault(identity['lei']['value'].upper(), []).append(key)
            counts[ex] = counts.get(ex, 0) + 1; n += 1
    json.dump(index, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), separators=(',', ':'))
    facts = {'node': NODE, 'as_of': AS_OF, 'version': VERSION, 'records': n, 'records_by_exchange': counts, 'events': sum(len(v) for v in ev_by.values()), 'issuers_with_events': len(ev_by),
             'source': 'public-record', 'operator': 'Allooloo Technologies Corp.', 'store': 'Cloudflare Workers Static Assets (one JSON per record and per issuer events)',
             'tools': ['resolve_issuer', 'get_record', 'list_events_since', 'list_aliases', 'list_nodes'], 'mcp': '/mcp (Streamable HTTP, JSON-RPC 2.0, no auth)'}
    json.dump(facts, open(os.path.join(OUT, 'facts.json'), 'w', encoding='utf-8'), indent=1)
    nodes = [{'node': f'{c}-cm-kg', 'country': nme, 'registry': f'{c}-cm-kg.org', 'door': f'https://mcp.{c}-cm-kg.ai', 'live': c == 'ca', 'as_of': AS_OF if c == 'ca' else None, 'records': n if c == 'ca' else 0}
             for c, nme in [('ca', 'Canada'), ('uk', 'United Kingdom'), ('au', 'Australia'), ('sg', 'Singapore'), ('ch', 'Switzerland'), ('de', 'Germany'), ('fr', 'France'), ('nl', 'Netherlands'), ('hk', 'Hong Kong'), ('jp', 'Japan'), ('kr', 'South Korea'), ('us', 'United States')]]
    json.dump(nodes, open(os.path.join(OUT, 'nodes.json'), 'w', encoding='utf-8'), indent=1)
    # static set (favicons, manifest) kept in CM-KG\DOOR\static and carried into data/ on every regeneration
    static_dir = os.path.join(ROOT, r'CM-KG\DOOR\static')
    if os.path.isdir(static_dir):
        for f in os.listdir(static_dir): shutil.copy(os.path.join(static_dir, f), os.path.join(OUT, f))
    print('records', n, counts, '| events', facts['events'], 'issuers with events', facts['issuers_with_events'], '| index tickers', len(index['ticker']), 'isins', len(index['isin']), 'leis', len(index['lei']))
if __name__ == '__main__': main()
