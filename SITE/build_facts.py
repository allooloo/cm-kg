r"""Generates the machine surface and the hero record from the records of record — never hand-typed.
  public/facts.json  and  public/.well-known/allooloo.json  <- COMPANY RECORDS\Allooloo_Domains_Master.xlsx (the single master; no dated copies, no backup beside it)
  public/hero.json                                           <- CM-KG\ISSUERS\ca-issuers.xlsx (fullest corporate row)
Run from C:\ALLOOLOO\SITE before deploy. A versioned copy of the master lands in CM-KG\POND\estate\domains\<date>\ on every build (pond rule)."""
import openpyxl, json, datetime, os, sys, shutil
AS_OF = datetime.date.today().isoformat()
# ---- domains: the exact master name (CEO, 2026-09-11); never a pattern match, never a backup written beside it
WB = r'C:\ALLOOLOO\COMPANY RECORDS\Allooloo_Domains_Master.xlsx'
if not os.path.exists(WB): sys.exit('domains master not found: ' + WB)
_pond = os.path.join(r'C:\ALLOOLOO\CM-KG\POND\estate\domains', AS_OF); _n = 1
while os.path.exists(_pond): _n += 1; _pond = os.path.join(r'C:\ALLOOLOO\CM-KG\POND\estate\domains', f'{AS_OF}-{_n}')
os.makedirs(_pond); shutil.copy(WB, os.path.join(_pond, 'Allooloo_Domains_Master.xlsx'))
wb = openpyxl.load_workbook(WB, read_only=True)
ws = wb['Build']; rows = list(ws.iter_rows(values_only=True)); hdr = [c for c in rows[0]]
domains = []
for r in rows[1:]:
    d = dict(zip(hdr, r))
    if d.get('Domain') and '.' in str(d['Domain']) and d.get('Group'):
        domains.append({'domain': d['Domain'], 'group': d['Group'], 'role': d['Role'], 'tld': d['TLD'], 'country': d.get('Country') or None, 'status': d['Status']})
assert len(domains) >= 51, len(domains)
print('domains master', WB, '| domains', len(domains), '| versioned copy', _pond)
facts = {
    'record': 'allooloo-facts', 'as_of': AS_OF,
    'legal_name': 'Allooloo Technologies Corp.', 'jurisdiction': 'Canada', 'city': 'Vancouver', 'country': 'CA',
    'positioning': 'Agentic Capital Markets Global Desk', 'masthead': '2027, today.',
    'url': 'https://allooloo.io', 'contact': 'https://allooloo.io/#contact',
    'products': [
        {'name': 'CM-KG', 'long_name': 'Capital Markets Knowledge Graph', 'root_domain': 'capitalmarketsknowledgegraph.ai', 'served_over': 'MCP (Model Context Protocol)'},
        {'name': 'CMR', 'long_name': 'Capital Markets Record', 'spec_domain': 'cm-record.org', 'keys': ['ISIN', 'ticker', 'LEI'], 'rule': 'one signed, versioned record per listed company; superseded, never deleted; every field names the registry it came from or the engine that read it'},
        {'name': 'AI ASK', 'long_name': 'AI assistant ask', 'door': 'ask.allooloo.io', 'status': 'named, not yet live'}],
    'nodes': [{'code': c, 'country': n, 'registry': f'{c}-cm-kg.org', 'door': f'{c}-cm-kg.ai', 'brand': f'{c}-cm-kg.com'} for c, n in
              [('ca', 'Canada'), ('uk', 'United Kingdom'), ('au', 'Australia'), ('sg', 'Singapore'), ('ch', 'Switzerland'), ('de', 'Germany'), ('fr', 'France'), ('nl', 'Netherlands'), ('hk', 'Hong Kong'), ('jp', 'Japan'), ('kr', 'South Korea'), ('us', 'United States')]],
    'engines': [{'name': 'Claude', 'duty': 'reader of record, CMR schema, adjudication'}, {'name': 'ChatGPT', 'duty': 'structured extraction at scale, second opinion'}, {'name': 'Google Gemini', 'duty': 'long-context filing reads'}, {'name': 'Perplexity', 'duty': 'grounded cold reads; search harvest'}, {'name': 'Grok', 'duty': 'real-time newswire, halt and resume signal'}, {'name': 'Mistral', 'duty': 'EU-node readers in their own languages; document AI on scanned filings'}, {'name': 'Tavily', 'duty': 'general web search layer'}, {'name': 'Cloudflare', 'duty': 'the network: Workers, embeddings, edge cache, every door'}],
    'licence_shapes': [{'name': 'Dealer MCP access licence'}, {'name': 'Issuer record licence'}, {'name': 'Knowledge Graph API licence'}, {'name': 'Node operator licence'}],
    'rules': ['licence only, no services', 'public-record only: no prices, no quotes, no licensed market data', 'blank is blank: nothing inferred; every enriched field carries a source and a reader', 'no engine is trusted alone; a person cuts the record before it is signed'],
    'proof': {'canada_width0': {'date': '2026-09-10', 'securities': 4820, 'corporate_issuers': 2851, 'exchanges': ['TSX', 'TSXV', 'CSE', 'Cboe Canada']}},
    'domains': domains,
    'social': {'x': 'https://x.com/allooloo_io', 'github': 'https://github.com/allooloo'},
}
os.makedirs('public/.well-known', exist_ok=True)
json.dump(facts, open('public/facts.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
json.dump(facts, open('public/.well-known/allooloo.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
# ---- hero record: fullest corporate row
wb = openpyxl.load_workbook(r'C:\ALLOOLOO\CM-KG\ISSUERS\ca-issuers.xlsx', read_only=True)
KEY = ['ISIN', 'LEI', 'Sector', 'Incorporation jurisdiction', 'SEDAR+ profile link', 'Transfer agent', 'Auditor', 'Newswire of habit', 'HQ city', 'HQ province/state', 'Listing date']
best = []
for ex in ['TSX', 'TSXV', 'CSE', 'Cboe Canada']:
    ws = wb[ex]; it = ws.iter_rows(values_only=True); hdr = next(it)
    for r in it:
        d = dict(zip(hdr, r))
        if not str(d['Security type']).startswith('Corporate'): continue
        best.append((sum(1 for k in KEY if d.get(k)), ex != 'TSX', d['Legal name'], d))
best.sort(key=lambda x: (-x[0], x[1], x[2]))
d = best[0][3]
def f(label, value, source, read_by, evidence=None, note=None):
    o = {'field': label, 'value': value or '', 'source': source or '', 'read_by': read_by or ''}
    if evidence: o['evidence'] = evidence
    if note: o['note'] = note
    return o
hero = {'record': 'CMR', 'version': 'width-0 draft', 'as_of': '2026-09-10', 'status': 'unsigned — signing lands with cm-record.org',
        'issuer': d['Legal name'], 'exchange': d['Exchange'], 'ticker': d['Ticker'],
        'fields': [
            f('Legal name', d['Legal name'], d['Roster source'], d['Roster read by']),
            f('Ticker', f"{d['Exchange']}: {d['Ticker']}", d['Roster source'], d['Roster read by']),
            f('ISIN', d['ISIN'], d['ISIN source'], d['ISIN read by']),
            f('LEI', d['LEI'], d['LEI source'], d['LEI read by'], note=f"registration {d['LEI registration status']}" if d.get('LEI registration status') else None),
            f('Sector', d['Sector'] + (f" — {d['Sub-sector']}" if d.get('Sub-sector') else ''), d['Sector source'], d['Sector read by']),
            f('Incorporation', d['Incorporation jurisdiction'], d['Jurisdiction source'], d['Jurisdiction read by']),
            f('Head office', ', '.join(x for x in [d['HQ city'], d['HQ province/state']] if x), d['HQ source'], d['HQ read by'], note='as recorded at GLEIF' if d['HQ city'] and d['HQ city'].lower() != 'vancouver' and 'vanvouver' in d['HQ city'].lower() else None),
            f('Transfer agent', d['Transfer agent'], d['Transfer agent source'], d['Transfer agent read by'], evidence=d.get('Transfer agent evidence')),
            f('Auditor', d['Auditor'], d['Auditor source'], d['Auditor read by'], evidence=d.get('Auditor evidence')),
            f('Newswire of habit', d['Newswire of habit'], (d.get('Newswire releases seen') or '').split('\n')[0], d['Newswire read by']),
            f('SEDAR+ profile', d['SEDAR+ profile link'], d['SEDAR+ source'], d['SEDAR+ read by']),
            f('Listed since', d['Listing date'] + (f" ({d['Listing type']})" if d.get('Listing type') else ''), d['Sector source'], d['Sector read by']),
        ],
        'gaps': d.get('Gaps') or ''}
json.dump(hero, open('public/hero.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('facts: domains', len(domains), '| hero:', hero['issuer'], hero['exchange'], hero['ticker'], '| fields filled', sum(1 for x in hero['fields'] if x['value']), '/', len(hero['fields']))
