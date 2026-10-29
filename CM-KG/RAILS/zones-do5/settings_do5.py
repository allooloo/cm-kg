r"""settings_do5.py — DAY ORDER 5 ZONES-01 (2026-10-24): the house zone settings on the 28 zones paid today.
SSL full (strict) · Always Use HTTPS · minimum TLS 1.2 · DNSSEC on · AI crawlers open (AI bots protection off, fight mode off, crawler protection off,
Cloudflare-managed robots.txt off — the zone serves its own robots.txt). Records, routes and bindings are other rails. Usage: python -X utf8 -I settings_do5.py read|apply"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cf import cf, zones
NEW = ('eu-eco.ai eu-issuer.ai eu-cm-kg.ai lu-eco.ai lu-issuer.ai lu-cm-kg.ai ky-eco.ai ky-issuer.ai ky-cm-kg.ai bm-eco.ai bm-issuer.ai bm-cm-kg.ai '
       'je-eco.ai je-issuer.ai je-cm-kg.ai in-issuer.ai in-cm-kg.ai tw-eco.ai tw-issuer.ai tw-cm-kg.ai sa-issuer.ai sa-cm-kg.ai ae-issuer.ai ae-cm-kg.ai '
       'br-issuer.ai br-cm-kg.ai mx-issuer.ai mx-cm-kg.ai').split()
MODE = sys.argv[1] if len(sys.argv) > 1 else 'read'
out = {}
for n in NEW:
    z = zones(n)[0]; Z = z['id']
    if MODE == 'apply':
        for k, v in (('ssl', 'strict'), ('always_use_https', 'on'), ('min_tls_version', '1.2')):
            cf('PATCH', f'/zones/{Z}/settings/{k}', {'value': v})
        cf('PUT', f'/zones/{Z}/bot_management', {'ai_bots_protection': 'disabled', 'fight_mode': False, 'crawler_protection': 'disabled', 'is_robots_txt_managed': False, 'enable_js': False})
        cf('PATCH', f'/zones/{Z}/dnssec', {'status': 'active'})
    ssl = (cf('GET', f'/zones/{Z}/settings/ssl').get('result') or {}).get('value')
    hs = (cf('GET', f'/zones/{Z}/settings/always_use_https').get('result') or {}).get('value')
    ds = cf('GET', f'/zones/{Z}/dnssec').get('result') or {}
    bm = cf('GET', f'/zones/{Z}/bot_management').get('result') or {}
    out[n] = {'id': Z, 'ssl': ssl, 'https': hs, 'dnssec': ds.get('status'), 'ds': ds.get('ds'), 'ai_bots': bm.get('ai_bots_protection'), 'fight': bm.get('fight_mode'), 'crawler': bm.get('crawler_protection'), 'robots_managed': bm.get('is_robots_txt_managed')}
    print(f"{n:16s} ssl={ssl} https={hs} dnssec={ds.get('status')} ai_bots={bm.get('ai_bots_protection')} fight={bm.get('fight_mode')} crawler={bm.get('crawler_protection')} robots={bm.get('is_robots_txt_managed')}")
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'settings-{MODE}-2026-10-24.json'), 'w'), indent=1)
