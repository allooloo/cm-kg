"""ORDER-034 (2026-10-22) — wire captures for the two standards pages: one get_record from the apex door (LSE:SHEL on the record) and one signed filing row from the Issuerwire door.
Read-only calls to the public doors; written to CM-KG\\ESTATE\\worker\\captures034.js (dated, beside any earlier capture). Run: python capture_034.py"""
import json, os, urllib.request, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'ESTATE', 'worker', 'captures034.js')
def call(url, name, args):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}}).encode()
    r = urllib.request.urlopen(urllib.request.Request(url, body, {'content-type': 'application/json', 'accept': 'application/json, text/event-stream', 'user-agent': 'Allooloo ORDER-034 capture'}), timeout=60)
    t = r.read().decode('utf-8')
    if 'data:' in t[:40]: t = [l[5:] for l in t.splitlines() if l.startswith('data:')][0]
    res = json.loads(t)['result']
    return res.get('structuredContent') or json.loads(res['content'][0]['text'])
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
rec = call('https://mcp.getissuer.ai/mcp', 'get_record', {'identifier': 'LSE:SHEL'})
idn = rec.get('identity', {})
kyp = {'captured': now, 'door': 'https://mcp.getissuer.ai/mcp', 'request': {'tool': 'get_record', 'arguments': {'identifier': 'LSE:SHEL'}},
       'response': {'cmr': rec.get('cmr'), 'node': rec.get('node'), 'as_of': rec.get('as_of'), 'version': rec.get('version'),
                    'identity': {k: idn[k] for k in ('name', 'isin', 'lei') if k in idn}}}
fl = call('https://mcp.issuerwire.ai/mcp', 'list_filings', {'issuer': 'SHEL', 'limit': 1})
rows = fl.get('rows') or fl.get('filings') or fl.get('items') or []
row = call('https://mcp.issuerwire.ai/mcp', 'get_row', {'id': rows[0]['id']}) if rows else fl   # the signed row in full: list_filings gives the id, get_row the row with its signature
iw = {'captured': now, 'door': 'https://mcp.issuerwire.ai/mcp', 'request': {'tool': 'get_row', 'arguments': {'id': rows[0]['id'] if rows else None}}, 'response': row}
if os.path.exists(OUT): os.replace(OUT, OUT + '.pre-' + now.replace(':', '').replace('-', ''))
with open(OUT, 'x', encoding='utf-8', newline='\n') as f:
    f.write('// ORDER-034 wire captures (capture_034.py) — read-only calls to the public doors; never typed.\n')
    f.write('export const KYP_CAPTURE = ' + json.dumps(kyp, ensure_ascii=False, indent=1) + ';\n')
    f.write('export const IW_CAPTURE = ' + json.dumps(iw, ensure_ascii=False, indent=1) + ';\n')
print(json.dumps(kyp, ensure_ascii=False)[:600]); print(json.dumps(iw, ensure_ascii=False)[:1500])
