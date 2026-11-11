r"""stack_pages.py — STACK-01 (2026-10-30) generator of the stack-pages Worker bundle (C:\ALLOOLOO\SITE\STACK-01\worker\bundle.js). Nothing typed:
§3 the trunk — eco-10060.org, rco-10060.org, acm-68000.org (+ acm-68000.ai, identical body at its own host): body from the canonical text v1.0 (trunk.py),
   machine files from each text's own schema, values from the wire (list_nodes, rco-records facts/health/jwks/tools, the chain's anchored tip) and the Book.
§6 the office pages — a2a-auditor.ai (verification), a2a-schema.ai (receipt v1 schema), acm-registry.org (the register): re-pointed to rco-records; the worked
   example is the chain's latest anchored tip, verified live at render by the Worker ({{LIVE_RECEIPT}}). Twins 301 to their canonical page.
§2 the six later members — the files site03a.py wrote to members2-out (hk ky bm je tw lu × .org/.ai/.com, identical bodies, no 301).
Footer on every page: "Standard held by Allooloo Technologies Corp. · Open standard, MIT licence." One expansion of RCO only. Usage: python -X utf8 -I stack_pages.py"""
import os, sys, json, re, html, glob, hashlib, datetime, subprocess, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import trunk
import au01_kit   # AUDIT-01 F1 (2026-11-11)
import clean01_kit   # CLEAN-01 item 5 (2026-11-11)
sys.path.insert(0, r'C:\ALLOOLOO\BOOK\rail'); import book
UA = {'User-Agent': 'Allooloo STACK-01 build (reads the wire; writes nothing on it)'}
def get(url):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40); return json.loads(r.read().decode('utf-8'))
def mcp(url, name, args=None, method='tools/call'):
    body = {'jsonrpc': '2.0', 'id': 1, 'method': method}; body['params'] = {'name': name, 'arguments': args or {}} if method == 'tools/call' else {}
    r = urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(body).encode(), headers={**UA, 'content-type': 'application/json', 'accept': 'application/json, text/event-stream'}), timeout=60)
    t = r.read().decode('utf-8'); j = json.loads(t[t.index('{'):]); res = j['result']
    return res if method != 'tools/call' else (res.get('structuredContent') or json.loads(res['content'][0]['text']))
NOW = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
# ---- the wire
ROSTER = mcp('https://mcp.getissuer.ai/mcp', 'list_nodes'); NODES = {n['node'].split('-')[0]: n for n in ROSTER['nodes'] if n.get('live')}
RFACTS = get('https://rco-records.ai/facts.json'); RHEALTH = get('https://rco-records.ai/health.json'); RJWKS = get('https://rco-records.ai/.well-known/jwks.json')
RTOOLS = mcp('https://mcp.rco-records.ai/mcp', None, method='tools/list')['tools']
# the chain's latest anchored tip (the rco-chain agent's anchor of record, ops rco/anchor/<night>.json), read with the signed-in az
env = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure')
k = subprocess.run(['az', 'storage', 'account', 'keys', 'list', '-n', 'allooloocmkgapex', '-g', 'allooloo-cmkg-shared', '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True, env=env, shell=True).stdout.strip()
from azure.storage.blob import BlobServiceClient
ops = BlobServiceClient('https://allooloocmkgapex.blob.core.windows.net', credential=k).get_container_client('ops')
an = sorted(b.name for b in ops.list_blobs(name_starts_with='rco/anchor/') if re.match(r'rco/anchor/\d{4}-\d{2}-\d{2}(-\d+)?\.json$', b.name))[-1]
ANCHOR = json.loads(ops.get_blob_client(an).download_blob().readall()); TIP = ANCHOR.get('anchor', ANCHOR)
rows = sorted(b.name for b in ops.list_blobs(name_starts_with='digest/rows/') if '/rco-chain' in b.name)
CHAINROW = json.loads(ops.get_blob_client(rows[-1]).download_blob().readall()) if rows else {}
SPOTS = [s for s in ((CHAINROW.get('anchor') or {}).get('spots') or [])]
TIPV = mcp('https://mcp.rco-records.ai/mcp', 'verify_receipt', {'id': TIP['id']})
assert TIPV['verification']['valid'], 'the anchored tip did not verify at build'
# ---- page shell (one look for the stack-pages hosts)
esc = lambda s: html.escape(str(s if s is not None else ''), quote=True)
link = lambda u, t=None: f'<a href="{esc(u)}">{esc(t or re.sub(r"^https?://", "", u).rstrip("/"))}</a>'
CSS = """*{margin:0;padding:0;box-sizing:border-box}body{background:#faf8f3;color:#1a1a1a;font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
.container{max-width:900px;margin:0 auto;padding:32px 24px 96px}.topbar{font-size:12px;color:#6b6b6b;letter-spacing:.04em;margin-bottom:14px}
.eyebrow{text-transform:uppercase;letter-spacing:.14em;color:#6b6b6b;font-size:11px;font-weight:600;margin:0 0 10px}h1{font:700 28px/1.2 ui-monospace,SFMono-Regular,Menlo,monospace;margin:0 0 4px}
h1 .host{display:block;font-size:14px;color:#c84a1e;font-weight:600;margin-top:6px}h2{font-size:18px;font-weight:700;margin:34px 0 12px;padding-bottom:8px;border-bottom:2px solid #c84a1e}
h3{font-size:15px;margin:22px 0 8px}p{margin:0 0 12px}.mission{font-size:17px;margin:18px 0 22px}.arrow{font-family:ui-monospace,monospace;font-size:13px;background:#f3eee0;padding:12px 14px;border-radius:4px}
.meta{font-size:13px;color:#6b6b6b}table{width:100%;border-collapse:collapse;font-size:13px;margin:12px 0 24px}th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #d4cfc1;vertical-align:top;overflow-wrap:anywhere}
th{background:#f3eee0;font-weight:700;font-size:12px;text-transform:uppercase;letter-spacing:.04em}a{color:#2455a3;text-decoration:none}code,.mono{font-family:ui-monospace,monospace;font-size:13px}
.surfaces{font-family:ui-monospace,monospace;font-size:12px;background:#1a1a1a;color:#f3eee0;padding:16px 20px;border-radius:4px;margin:12px 0 24px;white-space:pre-wrap;overflow-x:auto;line-height:1.7}
.ok{color:#2e7d32;font-weight:700}.bad{color:#c62828;font-weight:700}footer{margin-top:64px;padding-top:28px;border-top:1px solid #d4cfc1;font-size:12px;color:#6b6b6b;line-height:1.7}
form{display:grid;gap:6px;max-width:520px}form input,form textarea{font:inherit;padding:8px;border:1px solid #d4cfc1;border-radius:3px;background:#fff}form button{justify-self:start;padding:9px 16px;border:0;border-radius:3px;background:#c84a1e;color:#f3eee0}.hp{display:none}
@media (max-width:600px){.container{padding:24px 16px 72px}th,td{padding:7px}}"""
# CPG-02 (2026-10-31): the stack row of record is the members table of CPG-68000 v1.0 §5 — the seven, named as §5 names them, each linked to its standard's page
CPG = trunk.CANON['standards']['CPG-68000']; MEMT = next(b['table'] for sec in CPG['parts']['owns'] for b in sec['blocks'] if 'table' in b)
PAGE = {'ECO-10060': 'https://eco-10060.org/', 'SM-ECO-10060': 'https://sm-eco-10060.org/', 'ACM-68000': 'https://acm-68000.org/', 'AIO-10060': 'https://aio-10060.org/', 'AMP-10060': 'https://amp-10060.org/', 'RCO-10060': 'https://rco-10060.org/', 'CPG-68000': 'https://cpg-68000.org/',   # TWINS-01a: the canonical page is at cpg-68000.org/
       
        'ESG-10060': 'https://esg-10060.org/'}   # CEO confirmation (2026-10-31): esg-10060.org is ESG-10060's own zone (book-pages); sm-eco-10060.org/esg/ stays the second door
DESC = {'ESG-10060': 'https://esg-10060.org/esg-10060.json', 'ECO-10060': 'https://eco-10060.org/eco.json', 'SM-ECO-10060': 'https://sm-eco-10060.org/protocol.json', 'ACM-68000': 'https://acm-68000.org/.well-known/acm-68000.json', 'AIO-10060': 'https://aio-10060.org/aio-10060.json', 'AMP-10060': 'https://amp-10060.org/amp-10060.json', 'RCO-10060': 'https://rco-10060.org/rco.json', 'CPG-68000': 'https://cpg-68000.org/stack.json'}
EXP = {r[0]: r[1] for r in MEMT[1:]}
STACK_URL = 'https://cpg-68000.org/stack/6.json'   # TMKT-04: AIO-10060 v1.2 — stack 6; 1–5 stay as written · BOOK-05: ECO-10060 v1.2 — stack 5; 1–4 stay as written ·   # BOOK-03: AIO-10060 v1.1 — stack 4 (ECO 1.1, RCO 1.1, AIO 1.1); 1–3 stay as written ·   # AIO-01: ECO-10060 and RCO-10060 v1.1 — new editions, stack 3 (stacks 1 and 2 stay as written) ·   # the stack version record at a stable URL (CPG-68000 §7.1); /stack.json names the current one. TEXTS-02: v1.1 adds ESG-10060 — stack 2 (stack/1.json stays as written)
STACK_ROW = '<p class="stack">' + ' · '.join(f'<a href="{PAGE[r[0]]}">{esc(r[0])}</a>' for r in MEMT[1:]) + f' · <a href="{STACK_URL}">stack version</a></p>'
FOOT = f'<footer><p><b>{esc(trunk.HOLDER)}</b></p>{STACK_ROW}<p>RCO is the Record of Cleared Orders. Artificial intelligence makes mistakes; read the source.</p><p>© 2027 Allooloo Technologies Corp.</p></footer>'
def contact(host):
    return (f'<h2 id="contact">Contact</h2><p class="meta">Allooloo Technologies Corp. · Vancouver / London, UK</p><form action="https://formspree.io/f/moeqzgll" method="POST" accept-charset="UTF-8">'
            f'<input type="hidden" name="site" value="{esc(host)}"><input type="hidden" name="_subject" value="{esc(host)} contact"><input type="text" name="_gotcha" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">'
            '<label for="f-email">email</label><input id="f-email" type="email" name="email" required autocomplete="email"><label for="f-message">message</label><textarea id="f-message" name="message" rows="5" required></textarea><button type="submit">send</button></form>')
def page(host, title, eyebrow, body, desc):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>'
            f'<meta name="description" content="{esc(desc)}"><link rel="canonical" href="https://{esc(host)}/"><style>{CSS}</style></head><body><div class="container">'
            f'<div class="topbar">{esc(trunk.HOLDER)}</div><p class="eyebrow">{esc(eyebrow)}</p><h1>{esc(title)}<span class="host">{esc(host)}</span></h1>{body}{FOOT}</div></body></html>')
def card(host, name, desc, extra=None):
    c = {'protocolVersion': '0.3.0', 'name': name, 'description': desc, 'url': f'https://{host}/', 'provider': {'organization': 'Allooloo Technologies Corp.', 'url': 'https://allooloo.io'},
         'holder': 'Allooloo Technologies Corp.', 'licence': 'MIT', 'version': NOW[:10], 'capabilities': {'streaming': False, 'pushNotifications': False}, 'defaultInputModes': ['application/json'], 'defaultOutputModes': ['application/json', 'text/plain'],
         'skills': [], 'documentationUrl': f'https://{host}/llms.txt', 'kind': 'reference surface (serves no tools)'}
    c.update(extra or {}); return au01_kit.complete(c)   # AUDIT-01 F1: supportedInterfaces + one skill where missing (au01_kit.py)
OWN_FORM = {'a2a-auditor.ai', 'a2a-schema.ai', 'acm-registry.org'}   # MAIL-01: the sites whose page carries the contact form
SEC = lambda host: f'Contact: https://allooloo.io/security\nContact: {"https://" + host + "/#contact" if host in OWN_FORM else "https://allooloo.io/#contact"}\nExpires: 2027-10-30T00:00:00.000Z\nPreferred-Languages: en\nCanonical: https://{host}/.well-known/security.txt\n'
def J(o): return json.dumps(o, ensure_ascii=False, indent=1) + '\n'
BUNDLE = {}   # host -> path -> [content-type, body]
def put(host, path, body, ct=None):
    ct = ct or ('text/html; charset=utf-8' if path == '/' else 'application/json' if path.endswith('.json') or path.endswith('agent-card.json') else 'text/plain; charset=utf-8')
    BUNDLE.setdefault(host, {})[path] = [ct, body if isinstance(body, str) else J(body)]
def VER(std): return re.search(r'Version (\d+\.\d+)', trunk.CANON['standards'][std]['head'][2]).group(1)   # TEXTS-01: the version each text states (ACM-68000 1.1)
sys.path.insert(0, r'C:\ALLOOLOO\SITE\TEXTS-01'); import acm_first   # TEXTS-01: Agent Clearance Manifest written out once on first use
def trunk_site(host, std, eyebrow, descriptor):
    mis = trunk.mission(std); body = trunk.body_html(std)
    machine = '<h2>Machine surfaces</h2><p class="meta">' + ' · '.join(link(f'https://{host}{p}', p) for p in ['/llms.txt', '/.well-known/agent-card.json', '/.well-known/security.txt'] + [p for p in descriptor]) + '</p>'
    put(host, '/', page(host, std, eyebrow, body + machine, mis))
    put(host, '/llms.txt', f'# {host} — {std} · canonical text v{VER(std)}\n\n{trunk.body_text(std)}\nMachine: ' + ' · '.join(['/.well-known/agent-card.json', '/.well-known/security.txt'] + list(descriptor)) + f'\n\n{trunk.HOLDER}\n')
    put(host, '/.well-known/agent-card.json', card(host, f'{std} — canonical reference', mis, {'standard': std, 'standard_version': VER(std), 'descriptors': [f'https://{host}{p}' for p in descriptor]}))
    put(host, '/.well-known/security.txt', SEC(host))
    for p, o in descriptor.items(): put(host, p, o)
# ---- §3 ECO-10060: the node descriptor of ECO v1.0 §7.3 (eco.json) for every live node; values from list_nodes, the Book and the node's own surfaces
F73 = trunk.schema_fields('ECO-10060', '7.3')
def eco_desc(cc, n):
    ch = book.chapter(cc); f = book.eco_fields(ch) if ch else {}; d, dsrc = book.duty(ch) if ch else (None, None)
    reg = next((x for x in ch['sections']['ECO']['fields'] if x['name'] == 'competent_authorities'), {}) if ch else {}
    sto = next((x for x in ch['sections']['ECO']['fields'] if x['name'] == 'information_stores'), {}) if ch else {}
    v = {'standard': 'ECO-10060', 'standard_version': '1.0', 'schema_version': '0.1 (unratified)', 'market': cc, 'member': f'https://{cc}-eco-10060.org/', 'duty': d or 'not_found',
         'regulator': {'name': (f.get('regulator') or {}).get('value') or 'not_found', 'url': reg.get('source_url')}, 'store': {'name': (f.get('regulated_information_store') or {}).get('value') or 'not_found', 'url': sto.get('source_url')},
         'door': n.get('regional_door'), 'receipts_door': RFACTS['door'], 'jwks': f'https://{cc}-eco.ai/.well-known/jwks.json', 'status': 'live' if n.get('live') else 'provisioned', 'as_of': n.get('as_of'),
         'subject_types': 'not_found', 'book_chapter': ch['manifest']['version'] if ch else None}
    assert [k for k in F73 if k.rstrip('[]') not in v] == [], [k for k in F73 if k.rstrip('[]') not in v]
    return v
trunk_site('eco-10060.org', 'ECO-10060', f"Electronic Compliance Object · canonical text v{VER('ECO-10060')}",   # AIO-01: the text's own version

           {'/eco.json': {'standard': 'ECO-10060', 'standard_version': VER('ECO-10060'), 'schema': f"ECO-10060 v{VER('ECO-10060')} §7.3 — the node descriptor", 'fields': F73, 'record_schema': {'version': '0.2 (unratified)', 'source': f"ECO-10060 v{VER('ECO-10060')} §7.1", 'fields': next((x['fields'] for x in trunk.CANON['standards']['ECO-10060']['schemas'] if x['section'].startswith('7.1')), []), 'instrument_class': "the subject's class in the listing regime's own terms: the class name as that regime writes it, the provision or listing category it comes from, and the field's own source_url and source_date (not_found where the listing does not say)"}, 'read_at': NOW, 'roster': 'https://mcp.getissuer.ai/mcp list_nodes', 'nodes': [eco_desc(cc, NODES[cc]) for cc in sorted(NODES)]}})
# ---- §3 RCO-10060: the door descriptor of RCO v1.0 §10.1 (rco.json); values from the door's own facts, health, keyring and tools
F101 = trunk.schema_fields('RCO-10060', '10.1')
def requires(t):
    d = t.get('description', '')
    return 'writer' if 'writer token' in d else 'auditor_key' if t['name'] == 'issue_auditor_key' and False else 'firm_key' if re.search(r'customer key|your own|your slice|Authorization', d) else 'none'
rco = {'standard': 'RCO-10060', 'standard_version': '1.0', 'receipt_version': str(TIPV['receipt']['v']), 'receipt_versions': [{'version': '1', 'kid': k['kid'], 'status': k.get('status') or 'current'} for k in RJWKS['keys']],
       'verification_profile': 'not_found', 'jwks': RFACTS['keyring'], 'door': RFACTS['door'],
       'tools': [{'name': t['name'], 'purpose': re.split(r'(?<=\.)\s', t.get('description', ''))[0], 'requires': requires(t), 'returns': 'not_found'} for t in RTOOLS],
       'writers': 'not_found', 'rules': 'not_found', 'anchor': {'scheme': 'OpenTimestamps', 'calendars': [s['spot'] for s in SPOTS if str(s.get('spot', '')).startswith('https://')], 'schedule': 'nightly (rco-chain agent)', 'latest_tip': {'id': TIP['id'], 'seq': TIP['seq'], 'night': TIP.get('night'), 'verify': TIP.get('verify')}},
       'custody': {'append_only': True, 'off_platform_copy': {'bucket': (RHEALTH.get('export') or {}).get('bucket'), 'armed': (RHEALTH.get('export') or {}).get('armed'), 'last_put': (RHEALTH.get('export') or {}).get('last')}},
       'status': 'live' if RHEALTH.get('status') == 'ok' else 'not_found', 'read_at': NOW}
assert [k for k in F101 if k.rstrip('[]') not in rco] == [], [k for k in F101 if k.rstrip('[]') not in rco]
trunk_site('rco-10060.org', 'RCO-10060', f"Record of Cleared Orders · canonical text v{VER('RCO-10060')}", {'/rco.json': rco})   # AIO-01: the text's own version
# ---- §3 ACM-68000: the signal vocabulary (§6) and the register's attachments per market from the Book (Appendix B sections; revisions not yet populated)
SIGS = [{**s, 'state': s['reading'], 'action': s['boundary'], 'page': f"https://acm-{s['code'][4:]}.ai/", 'tlds': {'ai': f"acm-{s['code'][4:]}.ai"}} for s in trunk.signals()]
# TEXTS-01 (ACM-68000 v1.1 ruling): the earlier codes are reserved — listed in the register as reserved, never served, never reused; their zones forward to the standard's page
RESERVED = [{'code': f'ACM-{c}', 'state': 'reserved', 'served': False, 'reuse': 'never', 'zones_forward_to': 'https://acm-68000.org/', 'zones': [f'acm-{c}.{t}' for t in ('ai', 'com', 'org', 'io')]} for c in ('000', '300', '500')]
REVS = []   # the register revisions the Book holds (BOOK-02), each a Book record: rule_version in receipts does not move with them
for _p in sorted(glob.glob(os.path.join(book.ROOT, 'register', '*', '*.json'))):
    _r = json.load(open(_p, encoding='utf-8')); REVS.append({'rule_version': _r['rule_version'], 'rule_family': _r.get('rule_family'), 'duty': _r.get('duty'), 'path': book.rel(_p), 'content_hash': _r.get('content_hash'), 'chapter_evidence': (_r.get('chapter_evidence_ref') or {}).get('chapter'), 'published_at': _r.get('published_at')})
reg = {'standard': 'ACM-68000', 'standard_version': VER('ACM-68000'), 'schema': f"ACM-68000 v{VER('ACM-68000')} §8.1 — a register revision (unratified)", 'fields': trunk.schema_fields('ACM-68000', '8.1'),
       'revisions': REVS, 'revisions_note': 'register revisions held in the Book of Markets (BOOK-02); not promoted to the wire — rule_version values in receipts are the deployed strings', 'reserved': RESERVED,
       'chapter_attachments': [{'market': cc, 'chapter': book.chapter(cc)['manifest']['version'], 'acm_section': next(r['version'] for r in book.chapter(cc)['manifest']['sections'] if r['family'] == 'ACM'), 'duty_seed': book.duty(book.chapter(cc))[0]} for cc in book.markets()], 'read_at': NOW}
acm_desc = {'/signals.json': {'protocol': 'ACM-68000', 'expansion': 'Agent Clearance Manifest', 'standard_version': VER('ACM-68000'), 'source': f"ACM-68000 canonical text v{VER('ACM-68000')} §6", 'signals': SIGS, 'reserved': RESERVED, 'listing_status': 'a record attribute (trading, suspended, delisted) — never a signal'},
            '/.well-known/acm-68000.json': {'protocol': 'ACM-68000', 'expansion': 'Agent Clearance Manifest', 'standard_version': VER('ACM-68000'), 'reference': 'https://acm-68000.org/', 'reserved': [r['code'] for r in RESERVED], 'holder': 'Allooloo Technologies Corp.', 'licence': 'MIT', 'signals': [{'code': s['code'], 'reading': s['reading'], 'page': s['page']} for s in SIGS]},
            '/register.json': reg}
for h in ('acm-68000.org', 'acm-68000.ai'): trunk_site(h, 'ACM-68000', f"Clearance rules and the immutable rule register · canonical text v{VER('ACM-68000')}", acm_desc)
# ---- §6 the office pages
RV1 = next(b['table'] for sec in trunk.CANON['standards']['RCO-10060']['parts']['owns'] for b in sec['blocks'] if 'table' in b and b['table'][0][0] == 'Field')
LIVE = '{{LIVE_RECEIPT}}'
steps = f"""<h2>Verify a receipt — four reads, no account</h2>
<table><thead><tr><th>Step</th><th>Where</th><th>What it establishes</th></tr></thead><tbody>
<tr><td>1 · verify_receipt</td><td>{link(RFACTS['door'])} (MCP, public) · or GET {link('https://rco-records.ai/receipts/' + TIP['id'], 'rco-records.ai/receipts/{id}')}</td><td>The receipt's hash, id and Ed25519 signature recompute under the key named by kid ({link(RFACTS['keyring'], 'keyring')}).</td></tr>
<tr><td>2 · statement</td><td><code>get_statement</code> on {link(RFACTS['door'])} (your firm key) · or {link(RFACTS['x402']['routes']['statement'].split('?')[0], '/api/statement')} (x402)</td><td>The signed statement of your own slice for a month — the operator's attributable claim of completeness for that slice.</td></tr>
<tr><td>3 · OpenTimestamps tip</td><td>{', '.join(link(s['spot']) for s in SPOTS if str(s.get('spot', '')).startswith('https://'))}</td><td>The chain tip anchored nightly: seq {TIP['seq']:,} · {esc(TIP['id'])} · night {esc(TIP.get('night'))} — an independent witness that the chain existed then.</td></tr>
<tr><td>4 · AWS copy status</td><td>{link('https://rco-records.ai/health.json')} → export</td><td>Write-once copy in a second cloud: bucket {esc((RHEALTH.get('export') or {}).get('bucket'))} · armed {esc((RHEALTH.get('export') or {}).get('armed'))} · last put {esc(((RHEALTH.get('export') or {}).get('last') or {}).get('day'))} (status {esc(((RHEALTH.get('export') or {}).get('last') or {}).get('status'))}).</td></tr>
</tbody></table>
<h2>Worked example — the chain's latest anchored tip, verified as this page renders</h2>
{LIVE}"""
aud_body = f'<p class="mission"><b>{esc(trunk.mission("RCO-10060"))}</b></p>' + steps + contact('a2a-auditor.ai')
put('a2a-auditor.ai', '/', page('a2a-auditor.ai', 'Verify an RCO receipt', 'The auditor\'s page · rco-records', aud_body, 'Verify an RCO receipt: verify_receipt, the statement, the OpenTimestamps tip and the AWS copy, at rco-records.ai.'))
put('a2a-auditor.ai', '/llms.txt', f"# a2a-auditor.ai — verify an RCO receipt\n\n{trunk.mission('RCO-10060')}\n\n1. verify_receipt at {RFACTS['door']} (public) or GET https://rco-records.ai/receipts/{{id}}\n2. get_statement (firm key) or {RFACTS['x402']['routes']['statement']}\n3. OpenTimestamps tip: seq {TIP['seq']} {TIP['id']} (night {TIP.get('night')})\n4. AWS copy: https://rco-records.ai/health.json (export)\nKeyring: {RFACTS['keyring']}\n\n{trunk.HOLDER}\nOwner: Allooloo Technologies Corp. · Vancouver / London, UK\n")
put('a2a-auditor.ai', '/.well-known/agent-card.json', card('a2a-auditor.ai', 'Verify an RCO receipt', 'How an auditor verifies an RCO receipt at rco-records.ai: verify_receipt, the statement, the OpenTimestamps tip, the AWS copy.', {'door': RFACTS['door']}))
put('a2a-auditor.ai', '/.well-known/security.txt', SEC('a2a-auditor.ai'))
# a2a-schema.ai: receipt v1, regenerated from RCO-10060 v1.0 §5 (the field table) — the JSON Schema below is that table, nothing added
jsch = {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': 'https://a2a-schema.ai/receipt-v1.schema.json', 'title': 'RCO receipt version 1 (RCO-10060 v1.0 §5)', 'type': 'object',
        'required': [r[0] for r in RV1[1:] if r[3].lower().startswith('yes')], 'properties': {r[0]: {'type': {'integer': 'integer'}.get(r[1].split()[0], 'string'), 'description': r[2]} for r in RV1[1:]}}
sch_body = (f'<p class="mission"><b>{esc(trunk.mission("RCO-10060"))}</b></p><h2>Receipt version 1</h2><p class="meta">From RCO-10060 canonical text v1.0 §5. Machine form: {link("https://a2a-schema.ai/receipt-v1.schema.json", "/receipt-v1.schema.json")}.</p>'
            + trunk.block_html({'table': RV1}) + '<h2>A live receipt, verified as this page renders</h2>' + LIVE + contact('a2a-schema.ai'))
put('a2a-schema.ai', '/', page('a2a-schema.ai', 'RCO receipt · version 1', 'The receipt schema · rco-records', sch_body, 'The RCO receipt version 1 schema (RCO-10060 v1.0 §5), with a live receipt verified at render.'))
put('a2a-schema.ai', '/receipt-v1.schema.json', jsch)
put('a2a-schema.ai', '/llms.txt', '# a2a-schema.ai — RCO receipt version 1\n\n' + '\n'.join(f'- {r[0]} ({r[1]}): {r[2]}' for r in RV1[1:]) + f"\n\nSchema: https://a2a-schema.ai/receipt-v1.schema.json · door {RFACTS['door']}\n\n{trunk.HOLDER}\n")
put('a2a-schema.ai', '/.well-known/agent-card.json', card('a2a-schema.ai', 'RCO receipt version 1', 'The RCO receipt v1 field schema (RCO-10060 v1.0 §5).', {'schema': 'https://a2a-schema.ai/receipt-v1.schema.json'}))
put('a2a-schema.ai', '/.well-known/security.txt', SEC('a2a-schema.ai'))
# acm-registry.org: the register of the standards and their doors; the RCO row is mcp.rco-records.ai
REGROWS = [('SM-ECO-10060', 'https://sm-eco-10060.org/', 'jurisdiction binding · the Book of Markets chapters', None),
           ('ECO-10060', 'https://eco-10060.org/', 'the signed issuer record', 'https://mcp.getissuer.ai/mcp'),
           ('ACM-68000', 'https://acm-68000.org/', 'clearance rule reference and signal vocabulary', 'https://mcp.getissuer.ai/mcp (get_signal)'),
           ('RCO-10060', 'https://rco-10060.org/', 'RCO — Record of Cleared Orders: the signed receipt of a cleared read', RFACTS['door'])]
reg_body = ('<p class="meta">The register of the Allooloo-held standards and the doors that implement them. Every door is read from its own surface.</p><h2>The register</h2>'
            '<table><thead><tr><th>Standard</th><th>Owns</th><th>Door</th><th>Holder</th></tr></thead><tbody>'
            + ''.join(f'<tr><td>{link(u, s)}</td><td>{esc(o)}</td><td>{esc(d) if d else "—"}</td><td>Allooloo Technologies Corp.</td></tr>' for s, u, o, d in REGROWS) + '</tbody></table>'
            + f'<h2>The signal vocabulary</h2>' + trunk.block_html({'table': [['Signal', 'Reading', 'Boundary']] + [[s['code'], s['reading'], s['boundary']] for s in SIGS]})
            + '<h2>Reserved codes</h2>' + trunk.block_html({'table': [['Code', 'State', 'Zone']] + [[r['code'], 'reserved — never served, never reused', 'forwards to acm-68000.org'] for r in RESERVED]}) + contact('acm-registry.org'))
put('acm-registry.org', '/', page('acm-registry.org', 'The register', 'Allooloo-held standards and their doors', reg_body, 'The register of the Allooloo-held standards (SM-ECO-10060, ECO-10060, ACM-68000, RCO-10060) and their doors.'))
put('acm-registry.org', '/register.json', {'register': [{'standard': s, 'page': u, 'owns': o, 'door': d, 'holder': 'Allooloo Technologies Corp.'} for s, u, o, d in REGROWS], 'signals': [{'code': s['code'], 'reading': s['reading']} for s in SIGS], 'reserved': RESERVED, 'read_at': NOW})
put('acm-registry.org', '/llms.txt', '# acm-registry.org — the register\n\n' + '\n'.join(f'- {s}: {u} · {o} · door {d or "—"}' for s, u, o, d in REGROWS) + f'\n\n{trunk.HOLDER}\n')
put('acm-registry.org', '/.well-known/agent-card.json', card('acm-registry.org', 'The register of the Allooloo-held standards', 'SM-ECO-10060, ECO-10060, ACM-68000 and RCO-10060 with their doors; the RCO door is mcp.rco-records.ai.', {'register': 'https://acm-registry.org/register.json'}))
put('acm-registry.org', '/.well-known/security.txt', SEC('acm-registry.org'))
# ---- §2 the six later members (site03a.py output)
M2 = os.path.join(HERE, 'members2-out')
for hd in sorted(glob.glob(os.path.join(M2, '*'))):
    host = os.path.basename(hd)
    for fp in glob.glob(os.path.join(hd, '**', '*'), recursive=True, include_hidden=True):   # include_hidden: the .well-known files (addendum fix)
        if os.path.isdir(fp): continue
        rel = '/' + os.path.relpath(fp, hd).replace(os.sep, '/'); rel = '/' if rel == '/index.html' else rel
        ext = os.path.splitext(rel)[1]; ct = {'/': 'text/html; charset=utf-8', '.json': 'application/json', '.jsonld': 'application/ld+json', '.md': 'text/markdown; charset=utf-8', '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml', '.js': 'application/javascript'}.get('/' if rel == '/' else ext, 'application/json' if rel.split('/')[-1] in ('api-catalog', 'catalog', 'oauth-authorization-server', 'oauth-protected-resource', 'openid-configuration') else 'text/plain; charset=utf-8')
        put(host, rel, open(fp, encoding='utf-8').read(), ct)
# ---- §4 sri-10060.org and standard-10060.org: their snapshot of record (GREAT-CULL-02, the bytes the Pages project serves), with the DRIFT literals struck —
# "struck, not regenerated": the operator credit, the retired receipts door and zone, the typed counts. Every other byte as served.
SNAPS = r'C:\GREENCORE\AUDITS\GREAT-CULL-02-2026-10-10\snapshots'
STRIKE = [(r'<strong>Operator:</strong> Agentic KG Holdings &middot; reference operator &middot; MIT licen[cs]e(?: &middot; <a href="https://agent-kg\.ai/">agent-kg\.ai</a>)?', '<strong>Holder:</strong> Standard held by Allooloo Technologies Corp. &middot; Open standard, MIT licence.'),
          (r'&copy; 2026 Agentic KG Holdings &middot; reference operator(?: &middot; MIT licen[cs]e)?', '&copy; 2027 Allooloo Technologies Corp. &middot; MIT licence'),
          (r'Operator: Agentic KG Holdings · reference operator · MIT licen[cs]e(?: · agent-kg\.ai)?', 'Standard held by Allooloo Technologies Corp. · Open standard, MIT licence.'),
          (r'mcp\.rco-a2a\.ai/mcp', 'mcp.rco-records.ai/mcp'),
          (r' &middot; <a href="https://rco-10060\.org/">rco-10060\.org</a> &middot; <a href="https://rco-a2a\.ai/">rco-a2a\.ai</a>', ' &middot; <a href="https://rco-10060.org/">rco-10060.org</a>'),
          (r' &middot; <a href="https://rco-a2a\.ai/">rco-a2a\.ai</a>', ' &middot; <a href="https://rco-10060.org/">rco-10060.org</a>'),
          (r' \((?:50 nodes|50 sovereign nodes|49 members \+ apex|49 sovereign members \+ apex)\)', '')]
STRUCK = {}
for host in ():   # CPG-02: sri-10060.org and standard-10060.org are superseded pages now (below); their snapshots are no longer served
    hd = os.path.join(SNAPS, host); STRUCK[host] = 0
    for fp in glob.glob(os.path.join(hd, '**', '*'), recursive=True, include_hidden=True):   # include_hidden: the .well-known files (addendum fix)
        if os.path.isdir(fp) or '.pre' in os.path.basename(fp) or fp.endswith('manifest.json'): continue
        rel = '/' + os.path.relpath(fp, hd).replace(os.sep, '/').replace('.well-known__', '.well-known/'); rel = '/' if rel == '/index.html' else rel
        ext = os.path.splitext(rel)[1]
        if ext in ('.png', '.ico'): continue
        t = open(fp, encoding='utf-8', errors='replace').read()
        if ext == '.svg': put(host, rel, t, 'image/svg+xml'); continue   # served as Pages served it (text, no strike)
        for a, b in STRIKE: t, n = re.subn(a, b, t); STRUCK[host] += n
        ct = {'/': 'text/html; charset=utf-8', '.json': 'application/json', '.jsonld': 'application/ld+json', '.md': 'text/markdown; charset=utf-8', '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml', '.js': 'application/javascript', '.css': 'text/css'}.get('/' if rel == '/' else ext, 'text/plain; charset=utf-8')
        ct = {'api-catalog': 'application/linkset+json', 'catalog': 'application/json', 'oauth-authorization-server': 'application/json', 'oauth-protected-resource': 'application/json', 'openid-configuration': 'application/json'}.get(rel.split('/')[-1], ct)   # the content types the Pages middleware gave these names
        put(host, rel, t, ct)
print('struck from snapshots:', STRUCK)
# ---- CPG-02 (2026-10-31): the umbrella, its stack version record, and the held pages of the earlier era
import cpg02; cpg02.build(globals())
for _h, _paths in BUNDLE.items():   # TEXTS-01: the first-use expansion on every text surface of the bundle (JSON descriptors carry 'expansion' instead)
    for _p, _v in _paths.items():
        _k = 'html' if _v[0].startswith('text/html') else 'text' if _v[0].startswith(('text/plain', 'text/markdown')) else None
        if _k: _v[1] = acm_first.acm_first(_v[1], _k)
for _h, _paths in BUNDLE.items():   # CLEAN-01 item 5: the estate's Content-Signal line in every robots.txt of the bundle that states none (clean01_kit.py)
    if '/robots.txt' in _paths: _paths['/robots.txt'][1] = clean01_kit.robots(_paths['/robots.txt'][1])
TWINS = {'a2a-auditor.com': 'a2a-auditor.ai', 'a2a-auditor.io': 'a2a-auditor.ai', 'a2a-auditor.org': 'a2a-auditor.ai', 'a2a-schema.com': 'a2a-schema.ai', 'a2a-schema.io': 'a2a-schema.ai', 'acm-registry.com': 'acm-registry.org'}
# TWINS-01 (CEO 2026-11-01): eco-10060 and rco-10060 .ai/.com serve the .org body — the same bytes at their own host, no 301 (the live-twin rule)
ALIAS = {f'{s}.{t}': f'{s}.org' for s in ('eco-10060', 'rco-10060') for t in ('ai', 'com')}
LINK = {}   # TWINS-01a: the .org root is the page now and declares canonical in its HTML (TWINS-01's header on the descriptor root retired)
MACHINE = {'cpg-68000.org': {'/': '/cpg.json'}}   # TWINS-01a: the old root answers a machine caller (Accept without text/html) 301 → the descriptor
meta = {'built': NOW, 'tip': {'id': TIP['id'], 'seq': TIP['seq'], 'night': TIP.get('night')}, 'hosts': sorted(BUNDLE), 'twins': TWINS, 'alias': ALIAS, 'link': LINK, 'machine': MACHINE, 'hashes': {h: hashlib.sha256(BUNDLE[h]['/'][1].encode()).hexdigest() for h in BUNDLE if '/' in BUNDLE[h]}}
os.makedirs(os.path.join(HERE, 'worker'), exist_ok=True)
open(os.path.join(HERE, 'worker', 'bundle.js'), 'w', encoding='utf-8', newline='\n').write('// generated by stack_pages.py — do not edit by hand\nexport const BUNDLE = ' + json.dumps(BUNDLE, ensure_ascii=False) + ';\nexport const META = ' + json.dumps(meta, ensure_ascii=False) + ';\n')
json.dump(meta, open(os.path.join(HERE, f"bundle-meta-{NOW.replace(':', '').replace('-', '')}.json"), 'x', encoding='utf-8'), indent=1)
print('hosts', len(BUNDLE), 'files', sum(len(v) for v in BUNDLE.values()), 'bytes', sum(len(b) for v in BUNDLE.values() for _, b in v.values()), 'tip', TIP['id'])
