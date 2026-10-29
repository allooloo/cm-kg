r"""ORDER-037A (2026-10-23) — ACS SPF verification answered DnsRecordsNotMatched on '~all'; set the qualifier of the SPF record that acs_dns.py wrote to '-all'
(the IONOS includes stay, so the domain's IONOS mail still passes). Edits that one record in place (comment kept); touches nothing else.
  python acs_spf_qualifier.py <zone> <token file>"""
import json, sys, urllib.request
zone, tokf = sys.argv[1], sys.argv[2]; TOK = open(tokf, encoding='utf-8').read().strip()
def cf(method, path, body=None):
    r = urllib.request.Request('https://api.cloudflare.com/client/v4' + path, method=method, data=json.dumps(body).encode() if body else None, headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json'})
    try: return json.loads(urllib.request.urlopen(r, timeout=30).read())
    except urllib.error.HTTPError as e: return json.loads(e.read() or b'{}')
zid = cf('GET', f'/zones?name={zone}')['result'][0]['id']
OLD = 'v=spf1 include:spf.protection.outlook.com include:_spf-us.ionos.com include:_spf-eu.ionos.com ~all'
recs = [r for r in cf('GET', f'/zones/{zid}/dns_records?type=TXT&per_page=200')['result'] if r['content'].strip('"') == OLD]
if len(recs) != 1: raise SystemExit(f'{zone}: expected exactly one ORDER-037A SPF record, found {len(recs)} — nothing changed')
j = cf('PATCH', f"/zones/{zid}/dns_records/{recs[0]['id']}", {'content': OLD.replace(' ~all', ' -all')})
print(zone, 'SPF ->', 'v=spf1 ... -all' if j.get('success') else 'FAILED ' + json.dumps(j.get('errors'))[:200])
