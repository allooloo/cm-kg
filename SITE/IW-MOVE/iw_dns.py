r"""iw_dns.py — IW-MOVE-01 step 7: the door's nine host names at Cloudflare. The token is read in-process from AGENT KEYS, never printed.
  read <label>   every record of the nine hosts, their asuid.<host> and _dnsauth.<host> names -> dns-<label>.json (before / after)
  txt            for each host: asuid.<host> TXT gets the NEW environment's verification id as a second value (the old value stays, so the old door's
                 binding is untouched) — nothing public changes
  dnsauth <file> for each {host: token} in the file: _dnsauth.<host> TXT (the managed certificate's domain validation)
  flip           each host's proxied CNAME -> the new door's address (content only; proxy, TTL and everything else as they are). The before-state is
                 dns-before.json; `unflip` puts the old address back.
Usage: python -X utf8 -I iw_dns.py read before|after | txt | dnsauth <file> | flip | unflip"""
import json, sys, pathlib, urllib.request, urllib.error
H = pathlib.Path(__file__).parent; TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0]
HOSTS = ['issuerwire.ai', 'www.issuerwire.ai', 'mcp.issuerwire.ai', 'a2a-amn.ai', 'www.a2a-amn.ai', 'mcp.a2a-amn.ai', 'x402.a2a-amn.ai', 'agentmarketnews.ai', 'www.agentmarketnews.ai']
ZONES = ['issuerwire.ai', 'a2a-amn.ai', 'agentmarketnews.ai']; OLD = 'amn-door.jollyflower-416db105.francecentral.azurecontainerapps.io'; NEWV = '175AF0E31DACD3B43AED31539A8B75B948681DA48A4969DEE86DC2E5FC431ECF'
def cf(method, path, body=None):
    rq = urllib.request.Request('https://api.cloudflare.com/client/v4' + path, method=method, data=json.dumps(body).encode() if body is not None else None, headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json'})
    try: return json.loads(urllib.request.urlopen(rq, timeout=60).read())
    except urllib.error.HTTPError as e: return {'success': False, 'status': e.code, 'errors': json.loads(e.read() or b'{}').get('errors')}
Z = {}
for z in ZONES:
    r = cf('GET', f'/zones?name={z}'); Z[z] = r['result'][0]['id'] if r.get('success') and r['result'] else None
zone_of = lambda h: next(z for z in ZONES if h == z or h.endswith('.' + z))
def records(z):
    out = []; page = 1
    while True:
        r = cf('GET', f'/zones/{Z[z]}/dns_records?per_page=500&page={page}'); out += r.get('result') or []
        if page >= ((r.get('result_info') or {}).get('total_pages') or 1): return out
        page += 1
what = sys.argv[1]
if what == 'read':
    names = set(HOSTS) | {'asuid.' + h for h in HOSTS} | {'_dnsauth.' + h for h in HOSTS}; out = {'zones': Z, 'records': []}
    for z in ZONES:
        if not Z[z]: print(z, 'ZONE NOT REACHED BY THE TOKEN'); continue
        for r in records(z):
            if r['name'] in names: out['records'].append({k: r.get(k) for k in ('id', 'name', 'type', 'content', 'proxied', 'ttl')})
    json.dump(out, open(H / f'dns-{sys.argv[2]}.json', 'w'), indent=1)
    for r in sorted(out['records'], key=lambda r: (zone_of(r['name'].replace('asuid.', '').replace('_dnsauth.', '')), r['name'])): print(r['type'], r['name'], '->', r['content'][:80], 'proxied' if r['proxied'] else 'dns only')
if what == 'txt':
    for h in HOSTS:
        z = zone_of(h); have = [r for r in records(z) if r['name'] == 'asuid.' + h and r['type'] == 'TXT']
        if any(NEWV.lower() in r['content'].lower() for r in have): print('asuid.' + h, 'already carries the new id'); continue
        r = cf('POST', f'/zones/{Z[z]}/dns_records', {'type': 'TXT', 'name': 'asuid.' + h, 'content': f'"{NEWV}"', 'ttl': 60, 'comment': 'IW-MOVE-01: iw-env-francecentral (Allooloo) domain verification'}); print('asuid.' + h, 'added' if r.get('success') else f'FAILED {r.get("errors")}', '· kept', len(have))
if what == 'dnsauth':
    for h, tok in json.load(open(sys.argv[2])).items():
        z = zone_of(h); have = [r for r in records(z) if r['name'] == '_dnsauth.' + h and r['type'] == 'TXT']
        if any(tok in r['content'] for r in have): print('_dnsauth.' + h, 'already there'); continue
        r = cf('POST', f'/zones/{Z[z]}/dns_records', {'type': 'TXT', 'name': '_dnsauth.' + h, 'content': f'"{tok}"', 'ttl': 60, 'comment': 'IW-MOVE-01: managed certificate validation (Allooloo side)'}); print('_dnsauth.' + h, 'added' if r.get('success') else f'FAILED {r.get("errors")}')
if what in ('flip', 'unflip'):
    new = json.load(open(H / 'new-door.json'))['fqdn']; frm, to = (OLD, new) if what == 'flip' else (new, OLD); bad = 0
    for h in HOSTS:
        z = zone_of(h); rs = [r for r in records(z) if r['name'] == h and r['type'] in ('CNAME', 'A', 'AAAA')]
        if len(rs) != 1 or rs[0]['type'] != 'CNAME': print(h, 'NOT FLIPPED: expected one CNAME, found', [(r['type'], r['content']) for r in rs]); bad += 1; continue
        if rs[0]['content'] == to: print(h, 'already ->', to); continue
        if rs[0]['content'] != frm: print(h, 'NOT FLIPPED: points at', rs[0]['content']); bad += 1; continue
        r = cf('PATCH', f'/zones/{Z[z]}/dns_records/{rs[0]["id"]}', {'content': to}); print(h, '->', to if r.get('success') else f'FAILED {r.get("errors")}'); bad += not r.get('success')
    sys.exit(1 if bad else 0)
