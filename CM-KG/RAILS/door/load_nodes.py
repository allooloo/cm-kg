r"""Node-generic loader for the doors (replaces CM-KG\RAILS\ca-door\load.py from ORDER-010). Reads the CONFIRMED outputs of every live node:
   CM-KG\ISSUERS\<cc>-issuers.xlsx            -> one CMR v0 per row
   CM-KG\DISCLOSURE\events\<cc>-events.jsonl  -> events per issuer, newest first
and writes the door's data files under CM-KG\DOOR\data\ (Workers Static Assets; D1 and KV are refused by the account token):
   records/<node>/<EXCHANGE>/<TICKER>.json   events/<node>/<EXCHANGE>/<TICKER>.json   index.json (all nodes)   facts.json   nodes.json
Idempotent on (node, exchange, ticker): every file is rewritten from the workbook. Re-run after every weekly sweep, then `wrangler deploy` in CM-KG\DOOR.
Usage: python load_nodes.py [ca uk ...]   (default: every node with a workbook present). AS_OF_<CC> and CMR_VERSION_<CC> env vars per node."""
import openpyxl, json, os, re, datetime, sys, shutil
ROOT = r'C:\ALLOOLOO'; OUT = os.path.join(ROOT, r'CM-KG\DOOR\data')
NODES = [('ca', 'Canada'), ('uk', 'United Kingdom'), ('au', 'Australia'), ('sg', 'Singapore'), ('ch', 'Switzerland'), ('de', 'Germany'), ('fr', 'France'), ('nl', 'Netherlands'), ('hk', 'Hong Kong'), ('jp', 'Japan'), ('kr', 'South Korea'), ('us', 'United States')]
def slug_ticker(t): return re.sub(r'[^A-Za-z0-9.\-]', '_', str(t))
def gaps_of(text):
    out = {}
    for part in (text or '').split('; '):
        if ':' in part:
            f, why = part.split(':', 1); out[f.strip()] = why.strip()
    return out
def nkey(s): return re.sub(r'[^a-z0-9]+', ' ', str(s).lower().replace('&', ' and ')).strip()
# ---- per-node column maps: cmr field -> (value col, source col, read-by col, state col, gaps label)
CA = {'tabs': {'TSX': 'TSX', 'TSXV': 'TSXV', 'CSE': 'CSE', 'Cboe Canada': 'CBOE-CANADA'}, 'ticker': 'Ticker', 'name': 'Legal name', 'default_as_of': '2026-09-10',
      'fields': {'name': ('Legal name', 'Roster source', 'Roster read by', None, None), 'ticker': ('Ticker', 'Roster source', 'Roster read by', None, None), 'exchange': ('Exchange', 'Roster source', 'Roster read by', None, None),
                 'security_type': ('Security type', 'Sector source', 'Sector read by', None, None), 'isin': ('ISIN', 'ISIN source', 'ISIN read by', 'ISIN state', 'ISIN'), 'lei': ('LEI', 'LEI source', 'LEI read by', 'LEI state', 'LEI'),
                 'sector': ('Sector', 'Sector source', 'Sector read by', None, 'Sector'), 'jurisdiction': ('Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Incorporation jurisdiction state', 'Incorporation jurisdiction'),
                 'transfer_agent': ('Transfer agent', 'Transfer agent source', 'Transfer agent read by', 'Transfer agent state', 'Transfer agent'), 'auditor': ('Auditor', 'Auditor source', 'Auditor read by', 'Auditor state', 'Auditor'),
                 'newswire': ('Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire of habit state', 'Newswire of habit'), 'hq_city': ('HQ city', 'HQ source', 'HQ read by', None, 'HQ city'), 'hq_region': ('HQ province/state', 'HQ source', 'HQ read by', None, 'HQ province/state'),
                 'tier': ('Listing tier', 'Roster source', 'Roster read by', None, 'Listing tier'), 'sedar_profile': ('SEDAR+ profile link', 'SEDAR+ source', 'SEDAR+ read by', None, 'SEDAR+ profile link'), 'sedi_link': ('SEDI link (unverified — HTTP 403 on fetch)', None, 'SEDI read by', None, 'SEDI link')},
      'second': {'isin': 'ISIN', 'lei': 'LEI', 'transfer_agent': 'Transfer agent', 'auditor': 'Auditor', 'newswire': 'Newswire of habit', 'jurisdiction': 'Incorporation jurisdiction'}, 'prefixes': ['TSX', 'TSXV', 'CSE', 'CBOE-CANADA']}
UK = {'tabs': {'LSE Main Market': 'LSE', 'AIM': 'AIM', 'Aquis Stock Exchange': 'AQSE'}, 'ticker': 'Ticker (TIDM)', 'name': 'Legal name', 'default_as_of': '2026-09-11',
      'fields': {'name': ('Legal name', 'Roster source', 'Roster read by', None, None), 'ticker': ('Ticker (TIDM)', 'Roster source', 'Roster read by', None, None), 'exchange': ('Exchange', 'Roster source', 'Roster read by', None, None),
                 'market_segment': ('Market segment', 'Roster source', 'Roster read by', None, None), 'security_type': ('Security type', 'Roster source', 'Roster read by', None, None),
                 'isin': ('ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'ISIN'), 'sedol': ('SEDOL', 'SEDOL source', 'SEDOL read by', 'SEDOL State', 'SEDOL'), 'lei': ('LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI'),
                 'companies_house_number': ('Companies House number', 'Companies House source', 'Companies House read by', 'Companies House State', 'Companies House number'), 'companies_house_profile': ('Companies House profile link', 'Companies House source', 'Companies House read by', None, 'Companies House number'),
                 'registered_office': ('Registered office', 'Registered office source', 'Registered office read by', 'Registered office State', 'Registered office'), 'jurisdiction': ('Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State', 'Incorporation jurisdiction'),
                 'sic_codes': ('SIC code(s)', 'SIC source', 'SIC read by', 'SIC State', 'SIC code(s)'), 'sector': ('Sector (FTSE ICB)', 'Sector source', 'Sector read by', 'Sector State', 'Sector (FTSE ICB)'), 'sub_sector': ('Sub-sector', 'Sector source', 'Sector read by', None, None),
                 'auditor': ('Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Auditor'), 'accounts_filing': ('Accounts filing (Companies House)', None, 'Companies House read by', None, 'Companies House number'), 'accounts_period_end': ('Accounts period end', None, 'Accounts read by', None, None), 'going_concern': ('Going concern (accounts)', None, 'Accounts read by', None, None),
                 'registrar': ('Registrar', 'Registrar source', 'Registrar read by', 'Registrar State', 'Registrar'), 'newswire': ('Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State', 'Newswire of habit'),
                 'nsm_link': ('FCA NSM link (unverified — search entry)', None, 'NSM read by', None, 'FCA NSM link'), 'hq_city': ('HQ city', 'HQ source', 'HQ read by', 'HQ State', 'HQ city'), 'hq_country': ('HQ country', 'HQ source', 'HQ read by', None, 'HQ city'),
                 'website': ('Website', 'Website source', 'Website read by', None, None), 'admission_date': ('Admission date', 'Admission date source', 'Roster read by', None, 'Admission date')},
      'second': {'isin': 'ISIN', 'lei': 'LEI', 'companies_house_number': 'Companies House number', 'registrar': 'Registrar', 'auditor': 'Auditor', 'newswire': 'Newswire of habit', 'jurisdiction': 'Incorporation jurisdiction'}, 'prefixes': ['LSE', 'AIM', 'AQSE']}
MAPS = {'ca': CA, 'uk': UK}
def field(d, spec, gaps):
    vcol, scol, rcol, stcol, glabel = spec
    v = d.get(vcol)
    if v in (None, ''): return {'value': None, 'source_url': None, 'read_by': None, 'state': None, 'reason': gaps.get(glabel or vcol, 'no source read')}
    src = (d.get(scol) or '') if scol else ''
    if isinstance(src, str) and '\n' in src: src = src.split('\n')[0]
    st = (d.get(stcol) or 'sourced') if stcol else ('unverified' if 'unverified' in vcol else 'sourced')
    o = {'value': v if not isinstance(v, str) else v.strip(), 'source_url': src or None, 'read_by': d.get(rcol) or None, 'state': st}
    if isinstance(o['value'], str) and '[TMX workbook says' in o['value']:
        m = re.match(r'^(.*?)\s*\[TMX workbook says ([^\]]+)\]$', o['value'])
        if m and m.group(1).strip(): o['value'] = m.group(1).strip(); o['note'] = f'TMX workbook says {m.group(2)}'
        elif m: o['value'] = m.group(2).strip(); o['source_url'] = 'https://www.tsx.com/en/resource/571'; o['read_by'] = 'TMX listed-companies workbook (exchange list, monthly)'; o['state'] = 'sourced'
    if isinstance(o['value'], str) and '  [search by' in o['value']: o['value'], o['note'] = o['value'].split('  [', 1)[0], o['value'].split('  [', 1)[1].rstrip(']')
    return o
import pond  # pond rule 2: the loader reads the latest versioned outputs in POND\<node>\assembled\; the canonical ISSUERS / DISCLOSURE paths are the fallback for nodes assembled before the pond
def load_node(cc, index, facts_nodes):
    M = MAPS[cc]; node = f'{cc}-cm-kg'; host = f'https://mcp.{node}.ai'
    xlsx = pond.latest_assembled(node, f'{cc}-issuers.xlsx') or os.path.join(ROOT, rf'CM-KG\ISSUERS\{cc}-issuers.xlsx')
    evfn = pond.latest_assembled(node, f'{cc}-events.jsonl') or os.path.join(ROOT, rf'CM-KG\DISCLOSURE\events\{cc}-events.jsonl')
    print(node, 'inputs:', xlsx, '|', evfn)
    as_of = os.environ.get(f'AS_OF_{cc.upper()}', M['default_as_of']); version = int(os.environ.get(f'CMR_VERSION_{cc.upper()}', '1'))
    ev_by = {}
    if os.path.exists(evfn):
        for line in open(evfn, encoding='utf-8'):
            e = json.loads(line); ev_by.setdefault((e['exchange'], e['ticker']), []).append(e)
    wb = openpyxl.load_workbook(xlsx, read_only=True); n = 0; counts = {}
    for tab, exs in M['tabs'].items():
        ws = wb[tab]; it = ws.iter_rows(values_only=True); hdr = next(it)
        os.makedirs(os.path.join(OUT, 'records', node, exs), exist_ok=True); os.makedirs(os.path.join(OUT, 'events', node, exs), exist_ok=True)
        for row in it:
            d = dict(zip(hdr, row))
            if not d.get(M['ticker']): continue
            t = str(d[M['ticker']]).strip(); key = f'{node}/{exs}/{t}'; gaps = gaps_of(d.get('Gaps'))
            identity = {f: field(d, spec, gaps) for f, spec in M['fields'].items() if spec[0] in d}
            for f, col in M['second'].items():
                if f in identity and identity[f]['value'] is not None:
                    s2 = d.get(f'{col} second source'); r2 = d.get(f'{col} second read by')
                    if s2: identity[f]['second_source_url'] = str(s2).split('\n')[0]
                    if r2: identity[f]['second_read_by'] = r2
            aliases = []
            if d.get('Also known as'):
                names = [a.strip() for a in str(d['Also known as']).split(' | ')]; srcs = str(d.get('Alias source') or '').split('\n'); rbs = str(d.get('Alias read by') or '').split('\n')
                for i, a in enumerate(names):
                    if a: aliases.append({'value': a, 'source_url': srcs[i] if i < len(srcs) else None, 'read_by': rbs[i] if i < len(rbs) else None})
            evs = sorted(ev_by.get((tab, t), []), key=lambda e: e['date'], reverse=True)
            rec = {'cmr': key, 'node': node, 'as_of': as_of, 'version': version, 'identity': identity, 'aliases': aliases, 'events_url': f'{host}/events/{exs}/{t}', 'event_count': len(evs), 'gaps': [{'field': f, 'reason': w} for f, w in gaps.items()]}
            json.dump(rec, open(os.path.join(OUT, 'records', node, exs, slug_ticker(t) + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            json.dump([{k2: e.get(k2) for k2 in ('date', 'event_type', 'title', 'rns_category', 'ch_filing_type', 'wire', 'source', 'url', 'read_by', 'state', 'detail', 'second_source', 'second_read_by', 'period_end', 'statement_date', 'auditor_named', 'going_concern', 'extract_read_by') if e.get(k2) not in (None, '')} for e in evs],
                      open(os.path.join(OUT, 'events', node, exs, slug_ticker(t) + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            index['keys'].append(key); index['ticker'].setdefault(t.upper(), []).append(key)
            root = t.split('.')[0].upper()
            if root != t.upper(): index['ticker'].setdefault(root, []).append(key)
            for a in aliases: index['alias'].setdefault(nkey(a['value']), []).append(key)
            index['name'].setdefault(nkey(d[M['name']]), []).append(key)
            if identity.get('isin', {}).get('value'): index['isin'].setdefault(identity['isin']['value'].upper(), []).append(key)
            if identity.get('lei', {}).get('value'): index['lei'].setdefault(identity['lei']['value'].upper(), []).append(key)
            counts[exs] = counts.get(exs, 0) + 1; n += 1
    facts_nodes[node] = {'as_of': as_of, 'version': version, 'records': n, 'records_by_exchange': counts, 'events': sum(len(v) for v in ev_by.values()), 'issuers_with_events': len(ev_by), 'exchanges': list(M['tabs'].values())}
    print(node, 'records', n, counts, '| events', facts_nodes[node]['events'], 'issuers with events', len(ev_by))
def main():
    want = [a for a in sys.argv[1:] if a in MAPS] or [cc for cc in MAPS if os.path.exists(os.path.join(ROOT, rf'CM-KG\ISSUERS\{cc}-issuers.xlsx'))]
    index = {'ticker': {}, 'isin': {}, 'lei': {}, 'alias': {}, 'name': {}, 'keys': []}; facts_nodes = {}
    for sub in ('records', 'events'): os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    for cc in want: load_node(cc, index, facts_nodes)
    json.dump(index, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), separators=(',', ':'))
    facts = {'as_of': max(v['as_of'] for v in facts_nodes.values()), 'records': sum(v['records'] for v in facts_nodes.values()), 'events': sum(v['events'] for v in facts_nodes.values()), 'nodes': facts_nodes,
             'source': 'public-record', 'operator': 'Allooloo Technologies Corp.', 'store': 'Cloudflare Workers Static Assets (one JSON per record and per issuer events)',
             'tools': ['resolve_issuer', 'get_record', 'list_events_since', 'list_aliases', 'list_nodes'], 'mcp': '/mcp (Streamable HTTP, JSON-RPC 2.0, no auth)'}
    json.dump(facts, open(os.path.join(OUT, 'facts.json'), 'w', encoding='utf-8'), indent=1)
    nodes = [{'node': f'{c}-cm-kg', 'country': nme, 'registry': f'{c}-cm-kg.org', 'door': f'https://mcp.{c}-cm-kg.ai', 'live': f'{c}-cm-kg' in facts_nodes, 'as_of': facts_nodes.get(f'{c}-cm-kg', {}).get('as_of'), 'records': facts_nodes.get(f'{c}-cm-kg', {}).get('records', 0), 'exchanges': facts_nodes.get(f'{c}-cm-kg', {}).get('exchanges', [])} for c, nme in NODES]
    json.dump(nodes, open(os.path.join(OUT, 'nodes.json'), 'w', encoding='utf-8'), indent=1)
    static_dir = os.path.join(ROOT, r'CM-KG\DOOR\static')
    if os.path.isdir(static_dir):
        for f in os.listdir(static_dir): shutil.copy(os.path.join(static_dir, f), os.path.join(OUT, f))
    # retire the pre-ORDER-010 flat layout (records/<EX>/…) once the node layout exists: the same records live under records/ca-cm-kg/
    for sub in ('records', 'events'):
        for ex in ('TSX', 'TSXV', 'CSE', 'CBOE-CANADA'):
            p = os.path.join(OUT, sub, ex)
            if os.path.isdir(p) and os.path.isdir(os.path.join(OUT, sub, 'ca-cm-kg', ex)): shutil.rmtree(p)
    nfiles = sum(len(fs) for _, _, fs in os.walk(OUT))
    print('index tickers', len(index['ticker']), 'isins', len(index['isin']), 'leis', len(index['lei']), '| files in data/', nfiles, '(Workers static-assets cap 20,000 per version)')
    if nfiles > 20000: print('FILE CAP EXCEEDED — STOP per ORDER-010 Part A step 4')
if __name__ == '__main__': main()
