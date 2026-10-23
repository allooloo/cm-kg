"""ORDER-034 (2026-10-22) — SOVEREIGN NODES: the fifteen zones on the one Cloudflare account (GSC AI Agent Stack).
  python zones_034.py read            — per zone: id, status, DNS records, Workers custom domains, redirect rules, SSL mode, bot fight / AI-bot block, DNSSEC → zones-034\\state-<stamp>.json
  python zones_034.py bind            — bind apex + www of every zone as a Workers custom domain on estate-pages (Cloudflare writes the DNS records); prior state exported first
  python zones_034.py settings        — SSL full (strict), Always Use HTTPS on, AI-bot block off (bot_management.ai_bots_protection=disabled), DNSSEC on; prior values exported first
Tokens are read in-process from AGENT KEYS\\ by file name and never printed. Rule One: every change exports the prior value beside it (zones-034\\pre-<stamp>-<what>.json)."""
import json, os, sys, time, urllib.request, urllib.error, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); KEYS = r'C:\ALLOOLOO\AGENT KEYS'
ACCOUNT = 'dd2832b36f171b815f84c8487aada36b'; SERVICE = 'estate-pages'
NODES = 'ca uk us de fr nl ch au sg jp kr hk'.split()
ZONES = [f'{c}-issuer.ai' for c in NODES] + ['gb-issuer.ai', 'kyp-model.org', 'issuerwire.org']
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
def tok(name): return open(os.path.join(KEYS, name), encoding='utf-8').read().strip()
TOK = {n: tok(n) for n in ('cloudflare.txt', 'cloudflare-d1.txt')}
def cf(method, path, body=None, t='cloudflare.txt'):
    r = urllib.request.Request('https://api.cloudflare.com/client/v4' + path, data=json.dumps(body).encode() if body is not None else None, method=method,
                               headers={'Authorization': 'Bearer ' + TOK[t], 'content-type': 'application/json'})
    try: return json.load(urllib.request.urlopen(r, timeout=60))
    except urllib.error.HTTPError as e:
        try: return json.load(e)
        except Exception: return {'success': False, 'errors': [{'code': e.code, 'message': str(e)}]}
def zid(z): r = cf('GET', f'/zones?name={z}'); return r['result'][0]['id'] if r.get('result') else None
def save(name, obj):
    p = os.path.join(HERE, name)
    with open(p, 'x', encoding='utf-8', newline='\n') as f: json.dump(obj, f, ensure_ascii=False, indent=1)
    return p
def domains():
    out = []
    for t in ('cloudflare-d1.txt', 'cloudflare.txt'):
        r = cf('GET', f'/accounts/{ACCOUNT}/workers/domains?per_page=1000', t=t)
        if r.get('success'): return r['result'], t
        out.append((t, [e.get('code') for e in r.get('errors', [])]))
    return None, out
cmd = sys.argv[1] if len(sys.argv) > 1 else 'read'
if cmd == 'read':
    doms, how = domains(); state = {'read_at': STAMP, 'domains_token': how if doms is not None else None, 'domains_error': how if doms is None else None, 'zones': {}}
    for z in ZONES:
        i = zid(z); s = {'id': i}
        if not i: state['zones'][z] = s; continue
        dns = cf('GET', f'/zones/{i}/dns_records?per_page=100'); s['dns'] = [(d['type'], d['name'], d['content'], d['proxied']) for d in dns.get('result') or []] if dns.get('success') else ('ERR', [e.get('code') for e in dns.get('errors', [])])
        s['custom_domains'] = [(d['hostname'], d['service']) for d in (doms or []) if d.get('zone_name') == z]
        rr = cf('GET', f'/zones/{i}/rulesets/phases/http_request_dynamic_redirect/entrypoint'); s['redirects'] = [(r.get('expression'), (r.get('action_parameters') or {}).get('from_value', {}).get('target_url')) for r in (rr.get('result') or {}).get('rules', [])] if rr.get('success') else ('none' if any(e.get('code') == 10003 for e in rr.get('errors', [])) else ('ERR', [e.get('code') for e in rr.get('errors', [])]))
        ssl = cf('GET', f'/zones/{i}/settings/ssl'); s['ssl'] = (ssl.get('result') or {}).get('value') if ssl.get('success') else ('ERR', [e.get('code') for e in ssl.get('errors', [])])
        hs = cf('GET', f'/zones/{i}/settings/always_use_https'); s['always_https'] = (hs.get('result') or {}).get('value') if hs.get('success') else 'ERR'
        bm = cf('GET', f'/zones/{i}/bot_management'); s['bot_management'] = {k: (bm.get('result') or {}).get(k) for k in ('ai_bots_protection', 'fight_mode', 'crawler_protection')} if bm.get('success') else ('ERR', [e.get('code') for e in bm.get('errors', [])])
        ds = cf('GET', f'/zones/{i}/dnssec'); s['dnssec'] = (ds.get('result') or {}).get('status') if ds.get('success') else 'ERR'
        state['zones'][z] = s
    print(save(f'state-{STAMP}.json', state)); print(json.dumps(state, indent=1)[:6000])
elif cmd == 'bind':
    doms, how = domains()
    if doms is None: raise SystemExit(f'workers/domains not readable with any token: {how}')
    save(f'pre-{STAMP}-custom-domains.json', [d for d in doms if d.get('zone_name') in ZONES])
    for z in ZONES:
        i = zid(z)
        for h in (z, 'www.' + z):
            if any(d['hostname'] == h and d['service'] == SERVICE for d in doms): print(h, 'already bound'); continue
            r = cf('PUT', f'/accounts/{ACCOUNT}/workers/domains', {'environment': 'production', 'hostname': h, 'service': SERVICE, 'zone_id': i, 'override_existing_origin': True, 'override_existing_dns_record': True}, t=how)
            print(h, 'bound' if r.get('success') else ('FAILED', [(e.get('code'), e.get('message')) for e in r.get('errors', [])]))
elif cmd == 'settings':
    pre = {}
    for z in ZONES:
        i = zid(z); pre[z] = {}; res = []
        for k, v in (('ssl', 'strict'), ('always_use_https', 'on')):
            cur = cf('GET', f'/zones/{i}/settings/{k}'); pre[z][k] = (cur.get('result') or {}).get('value')
            if pre[z][k] != v: r = cf('PATCH', f'/zones/{i}/settings/{k}', {'value': v}); res.append(f"{k}={'ok' if r.get('success') else [e.get('code') for e in r.get('errors', [])]}")
            else: res.append(f'{k} already {v}')
        bm = cf('GET', f'/zones/{i}/bot_management'); pre[z]['bot_management'] = bm.get('result')
        if bm.get('success') and (bm['result'] or {}).get('ai_bots_protection') != 'disabled':
            r = cf('PUT', f'/zones/{i}/bot_management', {'ai_bots_protection': 'disabled'}); res.append(f"ai_bots_protection=disabled {'ok' if r.get('success') else [e.get('code') for e in r.get('errors', [])]}")
        else: res.append('ai-bot block already off' if bm.get('success') else f"bot_management unreadable {[e.get('code') for e in bm.get('errors', [])]}")
        ds = cf('GET', f'/zones/{i}/dnssec'); pre[z]['dnssec'] = (ds.get('result') or {}).get('status')
        if pre[z]['dnssec'] not in ('active', 'pending'): r = cf('PATCH', f'/zones/{i}/dnssec', {'status': 'active'}); res.append(f"dnssec={'ok' if r.get('success') else [e.get('code') for e in r.get('errors', [])]}")
        else: res.append(f"dnssec {pre[z]['dnssec']}")
        print(z, ' · '.join(res))
    save(f'pre-{STAMP}-settings.json', pre)
