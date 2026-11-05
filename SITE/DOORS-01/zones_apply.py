r"""zones_apply.py — DOORS-01 item 5: the getfilings, getticker, getauditor zones and the held stock on the wire (from ASOF-01's rail). Batch law: every zone is read and saved as it stood first
(backup\<zone>-as-read-<stamp>.json); only what is missing is written; nothing deleted, nothing repointed (an existing record, route or redirect rule that
differs stops that zone for the CEO's word). DNS is the house method of the estate's Worker-only hosts: proxied A 192.0.2.1 + AAAA 100:: (www a proxied CNAME).
  phase pages   getasof.ai          @ and www → Worker getasof-pages (the page)                                   role door
                getasof.com/.org/.io whole zone 301 → https://getasof.ai (path and query kept; one dynamic redirect rule)  role forward
                getshareprice.ai/.com/.org/.io  whole zone 301 → https://allooloo.io/ (held stock: no page, no llms.txt, no card)  role held
  phase door    mcp.getasof.ai and agent.getasof.ai → Worker cm-kg-apex (the router; run only after it carries the getasof profile)
  ledger        _estate TXT "estate:allooloo lens:Product family:products role:<door|forward|held> product:<getasof|getshareprice> doors01:2026-11-05"
as-of.ai and as-of.com: read; if not in the account they are named and skipped. Usage: python -X utf8 -I zones_apply.py pages|door plan|apply"""
import os, sys, json, time, datetime, urllib.request, urllib.error
PHASE, AP = sys.argv[1], 'apply' in sys.argv[2:]; HERE = os.path.dirname(os.path.abspath(__file__)); BK = os.path.join(HERE, 'backup'); os.makedirs(BK, exist_ok=True)
TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0]; ACCT = 'dd2832b36f171b815f84c8487aada36b'
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
def api(p, m='GET', b=None):
    for a in range(5):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request('https://api.cloudflare.com/client/v4' + p, method=m, headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json', 'User-Agent': 'Allooloo DOORS-01 zones'}, data=json.dumps(b).encode() if b is not None else None), timeout=30).read())
        except urllib.error.HTTPError as e:
            r = json.loads(e.read() or b'{}')
            if e.code == 429: time.sleep(5 * (a + 1)); continue
            return r
        except Exception: time.sleep(3)
    return {'success': False, 'errors': ['retries']}
ok = lambda r: 'ok' if r.get('success') else 'REFUSED ' + json.dumps(r.get('errors'))[:200]
TAG = lambda role, prod: f'"estate:allooloo lens:Product family:products role:{role} product:{prod} doors01:2026-11-05"'
DOORS = {'getfilings.ai': 'getfilings', 'getticker.ai': 'getticker', 'getauditor.ai': 'getauditor'}
FWD = {'getfilings.io': 'getfilings.ai', 'getticker.org': 'getticker.ai', 'getticker.io': 'getticker.ai', 'getauditor.org': 'getauditor.ai', 'getauditor.io': 'getauditor.ai'}
HELD = ['getfinancials.ai', 'getfinancials.io', 'getbonds.ai', 'getbonds.org', 'getbonds.io', 'getownership.ai', 'getownership.io', 'getownership.org', 'getdividends.ai', 'getdividends.io', 'getdividends.org']
PLAN = {'pages': {**{z: ('door', p, ['', 'www.'], 'getdoors-pages', None) for z, p in DOORS.items()},
                  **{z: ('forward', FWD[z].split('.')[0], ['', 'www.'], None, 'https://' + FWD[z]) for z in FWD},
                  **{z: ('held', z.split('.')[0], ['', 'www.'], None, 'https://allooloo.io/') for z in HELD}},
        'door': {z: ('door', p, ['mcp.', 'agent.'], 'cm-kg-apex', None) for z, p in DOORS.items()}}[PHASE]
log = {'phase': PHASE, 'apply': AP, 'at': STAMP}
for absent in ('getfilings.com', 'getfilings.org', 'getticker.com', 'getauditor.com'):
    z = api('/zones?name=' + absent).get('result') or []; log[absent] = 'in the account: ' + z[0]['id'] if z else 'not in the account — skipped'
    print(absent, log[absent])
for zone, (role, prod, hosts, script, target) in PLAN.items():
    Zr = api('/zones?name=' + zone)['result']; Z = Zr[0]['id']; L = log[zone] = {'zone_id': Z, 'plan': Zr[0]['plan']['name'], 'role': role, 'steps': []}
    recs = api(f'/zones/{Z}/dns_records?per_page=100').get('result') or []; routes = api(f'/zones/{Z}/workers/routes').get('result') or []
    rr = api(f'/zones/{Z}/rulesets/phases/http_request_dynamic_redirect/entrypoint'); rules = (rr.get('result') or {}).get('rules') or [] if rr.get('success') else []
    json.dump({'dns': recs, 'routes': routes, 'redirect_entrypoint': rr.get('result') if rr.get('success') else None}, open(os.path.join(BK, f'{zone}-as-read-{STAMP}.json'), 'w', encoding='utf-8'), indent=1)
    def step(what, fn): res = fn() if AP else {'success': True, 'plan': True}; L['steps'].append(f"{what}: {'planned' if not AP else ok(res)}"); print(zone, what, 'planned' if not AP else ok(res)); return res
    stop = None
    for h in hosts:
        name = (h + zone).rstrip('.') if h else zone; have = [r for r in recs if r['name'] == name]
        want = [('CNAME', zone)] if h == 'www.' else [('A', '192.0.2.1'), ('AAAA', '100::')]
        for t, c in want:
            ex = [r for r in have if r['type'] in ('A', 'AAAA', 'CNAME') and (r['type'] == t or (t != 'CNAME' and r['type'] == 'CNAME') or (t == 'CNAME' and r['type'] in ('A', 'AAAA')))]
            if any(r['type'] == t and r['content'].lower() == c.lower() and r.get('proxied') for r in ex): continue
            if ex: stop = f'{name}: a record already exists ({[(r["type"], r["content"]) for r in ex]}) — left for the CEO\'s word'; break
            step(f'dns {t} {name} → {c} (proxied)', lambda t=t, c=c, name=name: api(f'/zones/{Z}/dns_records', 'POST', {'type': t, 'name': name, 'content': c, 'proxied': True, 'ttl': 1, 'comment': 'DOORS-01 2026-11-05'}))
        if stop: break
        if script:
            pat = f'{name}/*'; r0 = [r for r in routes if r['pattern'] == pat]
            if r0 and r0[0].get('script') != script: stop = f'route {pat} exists on {r0[0].get("script")} — left for the CEO\'s word'; break
            if not r0: step(f'route {pat} → {script}', lambda pat=pat: api(f'/zones/{Z}/workers/routes', 'POST', {'pattern': pat, 'script': script}))
    if stop: L['stopped'] = stop; print(zone, 'STOP', stop); continue
    if target:
        expr = 'true'; tv = {'expression': f'concat("{target}", http.request.uri.path)'} if role == 'forward' else {'value': target}
        rule = {'action': 'redirect', 'description': f'DOORS-01 2026-11-05: whole zone 301 → {target}', 'expression': expr, 'enabled': True,
                'action_parameters': {'from_value': {'status_code': 301, 'target_url': tv, 'preserve_query_string': role == 'forward'}}}
        mine = [r for r in rules if (r.get('description') or '').startswith('DOORS-01')]
        if rules and not mine: L['stopped'] = f'the zone already carries {len(rules)} redirect rule(s) — left for the CEO\'s word'; print(zone, 'STOP', L['stopped']); continue
        if not mine: step(f'redirect rule (whole zone) 301 → {target}', lambda: api(f'/zones/{Z}/rulesets/phases/http_request_dynamic_redirect/entrypoint', 'PUT', {'rules': [rule]}))
    if PHASE == 'pages':
        tn = f'_estate.{zone}'; tv = TAG(role, prod); hv = [r for r in recs if r['name'] == tn and r['type'] == 'TXT']
        if not any(r['content'].strip('"') == tv.strip('"') for r in hv): step(f'ledger TXT {tn}', lambda: api(f'/zones/{Z}/dns_records', 'POST', {'type': 'TXT', 'name': tn, 'content': tv, 'ttl': 1, 'comment': 'DOORS-01 2026-11-05'}))
json.dump(log, open(os.path.join(HERE, f'zones-{PHASE}-{"apply" if AP else "plan"}-{STAMP}.json'), 'w', encoding='utf-8'), indent=1)
print('stopped zones:', [z for z, v in log.items() if isinstance(v, dict) and v.get('stopped')] or 'none')
