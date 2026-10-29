r"""zones03_kit.py — ZONES-03 (CEO order 2026-10-27): the ZONES-02 house kit on the nine new zones.
Per zone: SSL full (strict) · Always Use HTTPS · minimum TLS 1.2 · DNSSEC on (the DS lands at the registrar; one scheduled later check, no polling) ·
AI crawlers open (AI bots protection off, fight mode off, crawler protection off, Cloudflare-managed robots.txt off — the Worker serves robots.txt) ·
apex and www bound to the estate Worker (estate-pages) as Workers custom domains. The .ai of each family serves; every other zone 301s to it in the
Worker (zones03.js), path kept. Token in-process from AGENT KEYS\cloudflare.txt, never printed.
Usage: python -X utf8 -I zones03_kit.py read|apply   -> zones02-kit-<mode>-<date>.json beside"""
import sys, os, json, datetime
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\zones-do5')
from cf import cf, zones
ACCT = 'dd2832b36f171b815f84c8487aada36b'; SERVICE = 'estate-pages'
ZONES = 'data-replay.ai data-bench.ai data-cleanroom.ai data-review.ai data-score.ai data-timeline.ai data-events.ai data-cleanroom.io data-cleanroom.org'.split()
MODE = sys.argv[1] if len(sys.argv) > 1 else 'read'
bound = {d['hostname']: d['service'] for d in (cf('GET', f'/accounts/{ACCT}/workers/domains').get('result') or [])}
out = {}
for n in ZONES:
    z = zones(n)[0]; Z = z['id']
    if MODE == 'apply':
        for k, v in (('ssl', 'strict'), ('always_use_https', 'on'), ('min_tls_version', '1.2')):
            r = cf('PATCH', f'/zones/{Z}/settings/{k}', {'value': v})
            if not r.get('success'): print('  FAIL', n, k, r.get('errors'))
        r = cf('PUT', f'/zones/{Z}/bot_management', {'ai_bots_protection': 'disabled', 'fight_mode': False, 'crawler_protection': 'disabled', 'is_robots_txt_managed': False, 'enable_js': False})
        if not r.get('success'): print('  FAIL', n, 'bot_management', r.get('errors'))
        r = cf('PATCH', f'/zones/{Z}/dnssec', {'status': 'active'})
        if not r.get('success'): print('  FAIL', n, 'dnssec', r.get('errors'))
        for h in (n, 'www.' + n):
            if bound.get(h) == SERVICE: continue
            r = cf('PUT', f'/accounts/{ACCT}/workers/domains', {'hostname': h, 'service': SERVICE, 'environment': 'production', 'zone_id': Z})
            print('  bind', h, 'ok' if r.get('success') else r.get('errors'))
        bound = {d['hostname']: d['service'] for d in (cf('GET', f'/accounts/{ACCT}/workers/domains').get('result') or [])}
    ssl = (cf('GET', f'/zones/{Z}/settings/ssl').get('result') or {}).get('value')
    hs = (cf('GET', f'/zones/{Z}/settings/always_use_https').get('result') or {}).get('value')
    tls = (cf('GET', f'/zones/{Z}/settings/min_tls_version').get('result') or {}).get('value')
    ds = cf('GET', f'/zones/{Z}/dnssec').get('result') or {}
    bm = cf('GET', f'/zones/{Z}/bot_management').get('result') or {}
    dns = cf('GET', f'/zones/{Z}/dns_records?per_page=100').get('result') or []
    out[n] = {'id': Z, 'status': z['status'], 'ssl': ssl, 'https': hs, 'min_tls': tls, 'dnssec': ds.get('status'), 'ds': ds.get('ds'), 'ai_bots': bm.get('ai_bots_protection'), 'fight': bm.get('fight_mode'),
              'crawler': bm.get('crawler_protection'), 'robots_managed': bm.get('is_robots_txt_managed'), 'bound_apex': bound.get(n), 'bound_www': bound.get('www.' + n), 'dns': [f"{d['type']} {d['name']} {d.get('content', '')[:40]}" for d in dns]}
    o = out[n]; print(f"{n:18s} ssl={ssl} https={hs} tls={tls} dnssec={o['dnssec']} ai_bots={o['ai_bots']} fight={o['fight']} crawler={o['crawler']} robots={o['robots_managed']} apex->{o['bound_apex']} www->{o['bound_www']} dns={len(dns)}")
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'zones03-kit-{MODE}-{datetime.date.today().isoformat()}.json'), 'w'), indent=1)
