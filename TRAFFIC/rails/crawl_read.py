"""SITE-03B — read first, every zone on the account: bot_management (AI Crawl Control: ai_bots_protection, crawler_protection, content_bots_protection; Bot Fight Mode:
fight_mode; Super Bot Fight Mode: sbfm_* where the plan has it; managed robots.txt: is_robots_txt_managed), the WAF custom-rules entrypoint (rules that challenge or
block with a bot term in the expression), the WAF managed entrypoint (overrides that challenge), and on the wire: /robots.txt as served (Disallow lines, the Cloudflare
managed block, AI user agents disallowed) and /llms.txt presence. Read-only. Usage: python -X utf8 -I crawl_read.py <zones_all.json> <plan_site03.json> <out.json>"""
import json, sys, time, re, threading, concurrent.futures as cf, urllib.request, urllib.error
import requests
T = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt').read().strip(); H = {'Authorization': 'Bearer ' + T}; B = 'https://api.cloudflare.com/client/v4'
Z = json.load(open(sys.argv[1], encoding='utf-8'))['zones']; EST = {p['zone']: p['estate'] for p in json.load(open(sys.argv[2], encoding='utf-8'))}
AI_UAS = ['GPTBot', 'ChatGPT-User', 'OAI-SearchBot', 'ClaudeBot', 'Claude-Web', 'Claude-User', 'Claude-SearchBot', 'anthropic-ai', 'Google-Extended', 'PerplexityBot', 'Perplexity-User', 'CCBot', 'Applebot-Extended', 'Applebot', 'Bingbot', 'Amazonbot', 'Bytespider', 'cohere-ai', 'Diffbot', 'FacebookBot', 'meta-externalagent', 'YouBot', 'MistralAI-User', 'xAI-Grok', 'DuckAssistBot', 'omgili', 'Timpibot']
BOT_TERMS = re.compile(r'cf\.client\.bot|cf\.verified_bot|cf\.bot_management|verified_bot|known_bots|http\.user_agent', re.I)
lock = threading.Lock(); last = [0.0]; GAP = 0.25
def api(path):
    with lock:
        w = last[0] + GAP - time.time()
        if w > 0: time.sleep(w)
        last[0] = time.time()
    for attempt in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(B + path, headers=H), timeout=60))
        except urllib.error.HTTPError as e:
            try: return json.load(e)
            except Exception: return {'success': False, 'errors': [{'code': e.code}]}
        except Exception as e:
            if attempt == 3: return {'success': False, 'errors': [{'message': repr(e)[:100]}]}
            time.sleep(3 * (attempt + 1))
UA = {'User-Agent': 'Allooloo SITE-03B crawl read (read-only)'}
def robots(n):
    o = {'robots_status': None, 'robots_disallow': [], 'robots_ai_disallowed': [], 'robots_cf_managed': False, 'robots_sitemap': False, 'robots_served_by': ''}
    try:
        r = requests.get(f'https://{n}/robots.txt', headers=UA, timeout=25, allow_redirects=True); o['robots_status'] = r.status_code; o['robots_final_host'] = requests.utils.urlparse(r.url).hostname; o['robots_served_by'] = r.headers.get('server', '') + (' · surface ' + r.headers['x-surface-version'] if r.headers.get('x-surface-version') else '')
        if r.status_code == 200 and 'text' in (r.headers.get('content-type') or 'text'):
            t = r.text; o['robots_cf_managed'] = 'Cloudflare Managed' in t or 'managed by Cloudflare' in t.lower() or 'Content-Signal' in t and 'cloudflare' in t.lower()
            o['robots_sitemap'] = bool(re.search(r'^\s*sitemap\s*:', t, re.I | re.M))
            ua = '*'; dis = []
            for line in t.splitlines():
                l = line.strip()
                if not l or l.startswith('#'): continue
                m = re.match(r'(?i)user-agent\s*:\s*(.+)', l)
                if m: ua = m.group(1).strip(); continue
                m = re.match(r'(?i)disallow\s*:\s*(.*)', l)
                if m and m.group(1).strip(): dis.append((ua, m.group(1).strip()))
            o['robots_disallow'] = dis[:40]
            o['robots_ai_disallowed'] = sorted({u for u, p in dis if any(u.lower() == a.lower() for a in AI_UAS)} | ({'*'} if any(u == '*' and p == '/' for u, p in dis) else set()))
    except Exception as e: o['robots_status'] = 'error'; o['robots_error'] = repr(e)[:80]
    try: l = requests.get(f'https://{n}/llms.txt', headers=UA, timeout=20, allow_redirects=True); o['llms_status'] = l.status_code; o['llms_present'] = l.status_code == 200 and len(l.text) > 20 and 'text' in (l.headers.get('content-type') or 'text')
    except Exception: o['llms_status'] = 'error'; o['llms_present'] = False
    return o
def one(z):
    n = z['name']; zid = z['id']; o = {'zone': n, 'zone_id': zid, 'estate': EST.get(n, ''), 'plan': z['plan']}
    b = api(f'/zones/{zid}/bot_management'); r = b.get('result') or {}
    if b.get('success'): o.update({k: r.get(k) for k in ('ai_bots_protection', 'crawler_protection', 'content_bots_protection', 'fight_mode', 'is_robots_txt_managed', 'sbfm_definitely_automated', 'sbfm_likely_automated', 'sbfm_verified_bots', 'sbfm_static_resource_protection', 'enable_js', 'ai_training', 'ai_search', 'ai_user')}); o['bm_readable'] = True
    else: o['bm_readable'] = False; o['bm_error'] = str(b.get('errors'))[:120]
    c = api(f'/zones/{zid}/rulesets/phases/http_request_firewall_custom/entrypoint'); rules = ((c.get('result') or {}).get('rules') or []) if c.get('success') else []
    o['waf_custom_rules'] = len(rules); o['waf_custom_bot_rules'] = [{'id': x.get('id'), 'ruleset': (c.get('result') or {}).get('id'), 'action': x.get('action'), 'enabled': x.get('enabled'), 'expression': (x.get('expression') or '')[:160], 'description': (x.get('description') or '')[:80]} for x in rules if x.get('action') in ('challenge', 'managed_challenge', 'js_challenge', 'block') and BOT_TERMS.search(x.get('expression') or '')]
    m = api(f'/zones/{zid}/rulesets/phases/http_request_firewall_managed/entrypoint'); mr = ((m.get('result') or {}).get('rules') or []) if m.get('success') else []
    o['waf_managed_rules'] = len(mr); o['waf_managed_challenge_overrides'] = [{'id': x.get('id'), 'action': x.get('action'), 'enabled': x.get('enabled'), 'override_action': ((x.get('action_parameters') or {}).get('overrides') or {}).get('action'), 'description': (x.get('description') or '')[:80]} for x in mr if (((x.get('action_parameters') or {}).get('overrides') or {}).get('action') in ('challenge', 'managed_challenge', 'js_challenge', 'block'))]
    o.update(robots(n)); return o
t0 = time.time(); out = []
with cf.ThreadPoolExecutor(8) as ex:
    for i, r in enumerate(ex.map(one, Z), 1):
        out.append(r)
        if i % 200 == 0: print(i, 'zones', round(time.time() - t0), 's', flush=True)
json.dump({'read_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'zones': out}, open(sys.argv[3], 'w', encoding='utf-8'), indent=0)
from collections import Counter
print('done', len(out)); print('ai_bots', Counter(str(o.get('ai_bots_protection')) for o in out)); print('fight_mode', Counter(str(o.get('fight_mode')) for o in out)); print('sbfm_verified', Counter(str(o.get('sbfm_verified_bots')) for o in out)); print('managed robots', Counter(str(o.get('is_robots_txt_managed')) for o in out)); print('crawler_protection', Counter(str(o.get('crawler_protection')) for o in out))
print('waf custom bot rules', sum(len(o['waf_custom_bot_rules']) for o in out), 'zones', sum(1 for o in out if o['waf_custom_bot_rules'])); print('managed challenge overrides', sum(1 for o in out if o['waf_managed_challenge_overrides']))
print('robots status', Counter(str(o.get('robots_status')) for o in out)); print('robots with AI disallow', sum(1 for o in out if o['robots_ai_disallowed'])); print('robots cf-managed marker', sum(1 for o in out if o['robots_cf_managed'])); print('llms present', Counter(o.get('llms_present') for o in out))
