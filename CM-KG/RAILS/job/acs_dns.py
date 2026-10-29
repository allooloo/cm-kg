r"""ORDER-037A (2026-10-23) — write the Azure Communication Services Email verification records for a domain on Cloudflare, add-only (an identical record
already present is left; nothing is edited or deleted). Token read in-process from the key file, never printed.
  python acs_dns.py <zone> <token file> <records.json>      records.json = the domain's properties.verificationRecords from ARM
SPF: the domain carries no SPF today and its mailbox is IONOS (mx00/mx01.ionos.com), so the SPF written keeps IONOS: ACS's include + IONOS's, softfail."""
import json, sys, urllib.request
zone, tokf, recf = sys.argv[1], sys.argv[2], sys.argv[3]
TOK = open(tokf, encoding='utf-8').read().strip()
def cf(method, path, body=None):
    r = urllib.request.Request('https://api.cloudflare.com/client/v4' + path, method=method, data=json.dumps(body).encode() if body else None,
                               headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json'})
    try: return json.loads(urllib.request.urlopen(r, timeout=30).read())
    except urllib.error.HTTPError as e: return json.loads(e.read() or b'{}')
z = cf('GET', f'/zones?name={zone}')['result']
if not z: raise SystemExit(f'zone {zone} not on this token')
zid = z[0]['id']; rec = json.load(open(recf, encoding='utf-8'))
want = [('TXT', zone, rec['Domain']['value']),
        ('TXT', zone, 'v=spf1 include:spf.protection.outlook.com include:_spf-us.ionos.com include:_spf-eu.ionos.com ~all'),
        ('CNAME', f"{rec['DKIM']['name']}.{zone}", rec['DKIM']['value']),
        ('CNAME', f"{rec['DKIM2']['name']}.{zone}", rec['DKIM2']['value'])]
have = cf('GET', f'/zones/{zid}/dns_records?per_page=500')['result']
if any(r['type'] == 'TXT' and r['content'].strip('"').startswith('v=spf1') for r in have):
    want = [w for w in want if not w[2].startswith('v=spf1')]; print('SPF: a record already exists — left as is, not written (flag)')
for t, name, content in want:
    if any(r['type'] == t and r['name'] == name and r['content'].strip('"') == content for r in have): print(f'{t} {name}: present'); continue
    j = cf('POST', f'/zones/{zid}/dns_records', {'type': t, 'name': name, 'content': content, 'ttl': 3600, **({'proxied': False} if t == 'CNAME' else {}), 'comment': 'ORDER-037A ACS Email verification'})
    print(f"{t} {name}: {'written' if j.get('success') else 'FAILED ' + json.dumps(j.get('errors'))[:200]}")
