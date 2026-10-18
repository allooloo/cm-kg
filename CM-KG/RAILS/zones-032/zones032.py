r"""ORDER-032 C.4 — the five agent-swap zones (agent-swap.ai canonical; .com .io .org .co.uk 301 to it). Account GSC AI Agent Stack (dd2832b3…), the
one Cloudflare account of record for every root; token in-process from C:\ALLOOLOO\AGENT KEYS\cloudflare.txt, never printed.
  python zones032.py read      zone state: status, DNS records, SSL, bots, DNSSEC, Workers custom domains
  python zones032.py apply     SSL full (strict), always HTTPS, min TLS 1.2, AI-bot block OFF, bot fight OFF; bind each apex (and www) to the
                               estate-pages Worker as a custom domain. Create-only: an existing DNS record that blocks a binding is listed, never deleted.
Writes zones-032\state-<date>.json each run (new beside old)."""
import json, os, sys, datetime, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8')
ACCT = 'dd2832b36f171b815f84c8487aada36b'; ZONES = ['agent-swap.ai', 'agent-swap.com', 'agent-swap.io', 'agent-swap.org', 'agent-swap.co.uk']
TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0].strip()
def cf(method, path, body=None):
    req = urllib.request.Request('https://api.cloudflare.com/client/v4' + path, data=json.dumps(body).encode() if body is not None else None, method=method, headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read())
        except Exception: return {'success': False, 'errors': [{'code': e.code}]}
def zone(name): return (cf('GET', f'/zones?name={name}&account.id={ACCT}').get('result') or [None])[0]
def state():
    out = {}
    doms = cf('GET', f'/accounts/{ACCT}/workers/domains?per_page=1000').get('result') or []
    for n in ZONES:
        z = zone(n)
        if not z: out[n] = {'zone': 'NOT IN ACCOUNT'}; continue
        bm = cf('GET', f"/zones/{z['id']}/bot_management").get('result') or {}
        out[n] = {'id': z['id'], 'status': z['status'], 'plan': z['plan']['legacy_id'], 'ssl': (cf('GET', f"/zones/{z['id']}/settings/ssl").get('result') or {}).get('value'),
                  'always_https': (cf('GET', f"/zones/{z['id']}/settings/always_use_https").get('result') or {}).get('value'),
                  'dnssec': (cf('GET', f"/zones/{z['id']}/dnssec").get('result') or {}).get('status'), 'ai_bots': bm.get('ai_bots_protection'), 'fight_mode': bm.get('fight_mode'),
                  'dns': [(r['type'], r['name'], r['content'], r['proxied']) for r in (cf('GET', f"/zones/{z['id']}/dns_records?per_page=100").get('result') or [])],
                  'worker_domains': [(d['hostname'], d['service']) for d in doms if d.get('zone_name') == n]}
    return out
step = sys.argv[1] if len(sys.argv) > 1 else 'read'
if step == 'apply':
    for n in ZONES:
        z = zone(n)
        if not z: print(n, 'NOT IN ACCOUNT'); continue
        zid = z['id']; res = []
        for k, v in (('ssl', 'strict'), ('always_use_https', 'on'), ('min_tls_version', '1.2')):
            r = cf('PATCH', f'/zones/{zid}/settings/{k}', {'value': v}); res.append(f"{k}={'ok' if r.get('success') else r.get('errors')}")
        r = cf('PUT', f'/zones/{zid}/bot_management', {'ai_bots_protection': 'disabled', 'fight_mode': False}); res.append(f"bots={'ok' if r.get('success') else r.get('errors')}")
        r = cf('PATCH', f'/zones/{zid}/dnssec', {'status': 'active'}); res.append(f"dnssec={(r.get('result') or {}).get('status') if r.get('success') else r.get('errors')}")   # DS at the registrar is the scheduled later check
        recs = cf('GET', f'/zones/{zid}/dns_records?per_page=100').get('result') or []
        for host in (n, f'www.{n}'):
            block = [r for r in recs if r['name'] == host and r['type'] in ('A', 'AAAA', 'CNAME')]
            if block: res.append(f"{host}: DNS record present {[(r['type'], r['content']) for r in block]} — binding not attempted (Rule One: listed, not deleted)"); continue
            r = cf('PUT', f'/accounts/{ACCT}/workers/domains', {'hostname': host, 'service': 'estate-pages', 'environment': 'production', 'zone_id': zid})
            res.append(f"{host}: {'bound to estate-pages' if r.get('success') else r.get('errors')}")
        print(n, '·', ' · '.join(res))
st = state(); d = os.path.dirname(os.path.abspath(__file__)); fn = os.path.join(d, f'state-{datetime.date.today().isoformat()}-{step}.json')
json.dump(st, open(fn, 'w', encoding='utf-8'), indent=1)
for n, v in st.items(): print(n, json.dumps(v, ensure_ascii=False)[:400])
