"""START_ME_UP_5 §4 check 7 — read back the AI-bot posture on every zone in scope (Cloudflare bot_management: ai_bots_protection, crawler_protection,
fight_mode) and probe every surface with four crawler user-agents (PerplexityBot, ClaudeBot, GPTBot, Googlebot) expecting 200. Read-only; token in-process."""
import json, urllib.request, sys, datetime
sys.stdout.reconfigure(encoding='utf-8')
TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0].strip()
if '=' in TOK and ' ' not in TOK.split('=')[0]: TOK = TOK.split('=', 1)[1].strip()
H = {'authorization': 'Bearer ' + TOK, 'content-type': 'application/json'}
def cf(path):
    r = urllib.request.Request('https://api.cloudflare.com/client/v4' + path, headers=H)
    try:
        with urllib.request.urlopen(r, timeout=60) as x: return json.loads(x.read())
    except urllib.error.HTTPError as e: return {'errors': e.read()[:160].decode('utf-8', 'replace')}
NODES = ['ca', 'us', 'uk', 'fr', 'nl', 'ch', 'de', 'au', 'sg', 'jp', 'kr', 'hk']
PRODUCTS = ['trades', 'ask', 'coverage', 'esg', 'issuers', 'disclosure', 'registries', 'radar', 'x402']
SCOPE = ['allooloo.io'] + [f'agentic-{p}.ai' for p in PRODUCTS] + ['kyp-model.ai'] + [f'{cc}-cm-kg.ai' for cc in NODES]
UAS = {'PerplexityBot': 'Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)', 'ClaudeBot': 'Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)', 'GPTBot': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)', 'Googlebot': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
out = {}
for z in SCOPE:
    j = cf(f'/zones?name={z}'); zid = j['result'][0]['id'] if j.get('result') else None
    bm = (cf(f'/zones/{zid}/bot_management').get('result') or {}) if zid else {}
    posture = {k: bm.get(k) for k in ('ai_bots_protection', 'crawler_protection', 'fight_mode', 'enable_js', 'ai_bots_protection_default')} if bm else {'error': 'unreadable'}
    ua = {}
    for name, s in UAS.items():
        try:
            with urllib.request.urlopen(urllib.request.Request(f'https://{z}/', headers={'user-agent': s}), timeout=30) as r: ua[name] = r.status
        except urllib.error.HTTPError as e: ua[name] = e.code
        except Exception as e: ua[name] = str(e)[:40]
    out[z] = {'bot_management': posture, 'ua_probe': ua}
    print(f"{z:22s} ai_bots={posture.get('ai_bots_protection')} crawler={posture.get('crawler_protection')} fight={posture.get('fight_mode')} · " + ' '.join(f'{k}={v}' for k, v in ua.items()))
json.dump(out, open(rf'C:\ALLOOLOO\AZURE\bot-posture-{datetime.date.today()}.json', 'w'), indent=1)
