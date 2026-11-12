r"""zones_apply.py — USR-03: the getresearch zones on the wire (from DOORS-01's rail). Batch law: every zone is read and saved as it stood first
(backup\<zone>-as-read-<stamp>.json); only what is missing is written; nothing deleted, nothing repointed (an existing record, route or redirect rule that
differs stops that zone for the CEO's word). DNS is the house method of the estate's Worker-only hosts: proxied A 192.0.2.1 + AAAA 100:: (www a proxied CNAME).
  getresearch.ai                                   @ and www → Worker getresearch-pages (the page)                               role door
  getresearch.io · get-research.ai/.com/.org/.io   whole zone 301 → https://getresearch.ai (path and query kept; one redirect rule) role forward
  ledger   _estate TXT "estate:allooloo lens:Product family:products role:<door|forward> product:data-equityresearch usr04:2026-11-12"
The door itself is get_research on mcp.getissuer.ai (the apex router): no mcp. host on these zones. Usage: python -X utf8 -I zones_apply.py plan|apply"""
import os, sys, json, time, datetime, urllib.request, urllib.error
AP = 'apply' in sys.argv[1:]; HERE = os.path.dirname(os.path.abspath(__file__)); BK = os.path.join(HERE, 'backup'); os.makedirs(BK, exist_ok=True)
TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0]
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
def api(p, m='GET', b=None):
    for a in range(5):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request('https://api.cloudflare.com/client/v4' + p, method=m, headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json', 'User-Agent': 'Allooloo USR-01 zones'}, data=json.dumps(b).encode() if b is not None else None), timeout=30).read())
        except urllib.error.HTTPError as e:
            r = json.loads(e.read() or b'{}')
            if e.code == 429: time.sleep(5 * (a + 1)); continue
            return r
        except Exception: time.sleep(3)
    return {'success': False, 'errors': ['retries']}
ok = lambda r: 'ok' if r.get('success') else 'REFUSED ' + json.dumps(r.get('errors'))[:200]
TAG = lambda role: f'"estate:allooloo lens:Product family:products role:{role} product:data-equityresearch usr04:2026-11-12"'
FWD = ['data-equityresearch.com', 'data-equityresearch.org', 'data-equityresearch.io', 'dataequityresearch.ai', 'dataequityresearch.com', 'dataequityresearch.org', 'dataequityresearch.io']
PLAN = {'data-equityresearch.ai': ('shelf', ['', 'www.'], 'getresearch-pages', None), **{z: ('forward', ['', 'www.'], None, 'https://data-equityresearch.ai') for z in FWD}}
log = {'apply': AP, 'at': STAMP}; bad = 0
for zone, (role, hosts, script, target) in PLAN.items():
    Zr = api('/zones?name=' + zone).get('result') or []
    if not Zr: log[zone] = 'not in the account — skipped'; print(zone, log[zone]); continue
    Z = Zr[0]['id']; L = log[zone] = {'zone_id': Z, 'plan': Zr[0]['plan']['name'], 'status': Zr[0]['status'], 'role': role, 'steps': []}
    recs = api(f'/zones/{Z}/dns_records?per_page=100').get('result') or []; routes = api(f'/zones/{Z}/workers/routes').get('result') or []
    rr = api(f'/zones/{Z}/rulesets/phases/http_request_dynamic_redirect/entrypoint'); rules = (rr.get('result') or {}).get('rules') or [] if rr.get('success') else []
    json.dump({'dns': recs, 'routes': routes, 'redirect_entrypoint': rr.get('result') if rr.get('success') else None}, open(os.path.join(BK, f'{zone}-as-read-{STAMP}.json'), 'w', encoding='utf-8'), indent=1)
    def step(what, fn):
        global bad
        res = fn() if AP else {'success': True}; L['steps'].append(f"{what}: {'planned' if not AP else ok(res)}"); print(zone, what, 'planned' if not AP else ok(res)); bad += 0 if res.get('success') else 1; return res
    stop = None
    for h in hosts:
        name = (h + zone) if h else zone; have = [r for r in recs if r['name'] == name]
        want = [('CNAME', zone)] if h == 'www.' else [('A', '192.0.2.1'), ('AAAA', '100::')]
        for t, c in want:
            ex = [r for r in have if r['type'] in ('A', 'AAAA', 'CNAME') and (r['type'] == t or (t != 'CNAME' and r['type'] == 'CNAME') or (t == 'CNAME' and r['type'] in ('A', 'AAAA')))]
            if any(r['type'] == t and r['content'].lower() == c.lower() and r.get('proxied') for r in ex): continue
            if ex: stop = f'{name}: a record already exists ({[(r["type"], r["content"]) for r in ex]}) — left for the CEO\'s word'; break
            step(f'dns {t} {name} → {c} (proxied)', lambda t=t, c=c, name=name: api(f'/zones/{Z}/dns_records', 'POST', {'type': t, 'name': name, 'content': c, 'proxied': True, 'ttl': 1, 'comment': 'USR-04 2026-11-12'}))
        if stop: break
        if script:
            pat = f'{name}/*'; r0 = [r for r in routes if r['pattern'] == pat]
            if r0 and r0[0].get('script') != script: stop = f'route {pat} exists on {r0[0].get("script")} — left for the CEO\'s word'; break
            if not r0: step(f'route {pat} → {script}', lambda pat=pat: api(f'/zones/{Z}/workers/routes', 'POST', {'pattern': pat, 'script': script}))
    if stop: L['stopped'] = stop; print(zone, 'STOP', stop); bad += 1; continue
    if target:
        rule = {'action': 'redirect', 'description': f'USR-04 2026-11-12: whole zone 301 → {target}', 'expression': 'true', 'enabled': True,
                'action_parameters': {'from_value': {'status_code': 301, 'target_url': {'expression': f'concat("{target}", http.request.uri.path)'}, 'preserve_query_string': True}}}
        mine = [r for r in rules if (r.get('description') or '').startswith('USR-04')]
        if rules and not mine: L['stopped'] = f'the zone already carries {len(rules)} redirect rule(s) — left for the CEO\'s word'; print(zone, 'STOP', L['stopped']); bad += 1; continue
        if not mine: step(f'redirect rule (whole zone) 301 → {target}', lambda: api(f'/zones/{Z}/rulesets/phases/http_request_dynamic_redirect/entrypoint', 'PUT', {'rules': [rule]}))
    tn = f'_estate.{zone}'; tv = TAG(role); hv = [r for r in recs if r['name'] == tn and r['type'] == 'TXT']
    if not any(r['content'].strip('"') == tv.strip('"') for r in hv): step(f'ledger TXT {tn}', lambda: api(f'/zones/{Z}/dns_records', 'POST', {'type': 'TXT', 'name': tn, 'content': tv, 'ttl': 1, 'comment': 'USR-04 2026-11-12'}))
json.dump(log, open(os.path.join(HERE, f'zones-shelf-{"apply" if AP else "plan"}-{STAMP}.json'), 'w', encoding='utf-8'), indent=1)
print('failed or stopped steps:', bad); sys.exit(1 if bad else 0)
