"""SITE-03B — the AFTER read: bot_management re-read on every zone the apply touched, and robots.txt re-fetched on the zones whose managed robots.txt was turned off;
every other zone's row is carried from the BEFORE read (unchanged). Usage: python -X utf8 -I crawl_after.py <crawl_state.json> <crawl_apply.json> <after.json>"""
import json, sys, time, re, threading, urllib.request, urllib.error, concurrent.futures as cf
import requests
T = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt').read().strip(); H = {'Authorization': 'Bearer ' + T}; B = 'https://api.cloudflare.com/client/v4'
C = json.load(open(sys.argv[1], encoding='utf-8')); A = json.load(open(sys.argv[2], encoding='utf-8'))
changed = {z['zone'] for z in A['zones'] if z['actions']}; robots_again = {z['zone'] for z in A['zones'] for a in z['actions'] if 'is_robots_txt_managed' in a['action']}
lock = threading.Lock(); last = [0.0]
def api(path):
    with lock:
        w = last[0] + 0.25 - time.time()
        if w > 0: time.sleep(w)
        last[0] = time.time()
    try: return json.load(urllib.request.urlopen(urllib.request.Request(B + path, headers=H), timeout=60))
    except Exception as e: return {'success': False, 'errors': [{'message': repr(e)[:80]}]}
AI = ['GPTBot', 'ChatGPT-User', 'OAI-SearchBot', 'ClaudeBot', 'Claude-Web', 'Claude-User', 'Claude-SearchBot', 'anthropic-ai', 'Google-Extended', 'PerplexityBot', 'Perplexity-User', 'CCBot', 'Applebot-Extended', 'Applebot', 'Bingbot', 'Amazonbot', 'Bytespider', 'cohere-ai', 'Diffbot', 'FacebookBot', 'meta-externalagent', 'YouBot', 'MistralAI-User', 'xAI-Grok', 'DuckAssistBot', 'omgili', 'Timpibot']
def one(o):
    o = dict(o); n = o['zone']
    if n in changed:
        b = api(f"/zones/{o['zone_id']}/bot_management"); r = b.get('result') or {}
        if b.get('success'): o.update({k: r.get(k) for k in ('ai_bots_protection', 'crawler_protection', 'content_bots_protection', 'fight_mode', 'is_robots_txt_managed', 'sbfm_verified_bots')})
    if n in robots_again:
        try:
            r = requests.get(f'https://{n}/robots.txt', headers={'User-Agent': 'Allooloo SITE-03B after read'}, timeout=25); t = r.text if r.status_code == 200 else ''
            o['robots_status'] = r.status_code; o['robots_cf_managed'] = 'Cloudflare Managed' in t or ('Content-Signal' in t and 'cloudflare' in t.lower()); o['robots_sitemap'] = bool(re.search(r'^\s*sitemap\s*:', t, re.I | re.M))
            ua = '*'; dis = []
            for line in t.splitlines():
                l = line.strip(); m = re.match(r'(?i)user-agent\s*:\s*(.+)', l)
                if m: ua = m.group(1).strip(); continue
                m = re.match(r'(?i)disallow\s*:\s*(.*)', l)
                if m and m.group(1).strip(): dis.append((ua, m.group(1).strip()))
            o['robots_disallow'] = dis[:40]; o['robots_ai_disallowed'] = sorted({u for u, p in dis if any(u.lower() == a.lower() for a in AI)} | ({'*'} if any(u == '*' and p == '/' for u, p in dis) else set()))
        except Exception as e: o['robots_status'] = 'error'
    return o
with cf.ThreadPoolExecutor(6) as ex: out = list(ex.map(one, C['zones']))
json.dump({'read_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'zones': out}, open(sys.argv[3], 'w', encoding='utf-8'), indent=0)
from collections import Counter
print('after: ai_bots', Counter(str(o.get('ai_bots_protection')) for o in out), 'managed robots', Counter(str(o.get('is_robots_txt_managed')) for o in out), 'cf-managed marker', sum(1 for o in out if o.get('robots_cf_managed')), 'AI disallow', sum(1 for o in out if o.get('robots_ai_disallowed')))
