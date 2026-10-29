"""SITE-03B §5 — from the wire: 20 sampled Allooloo zones and 20 sampled GSC zones, apex fetched as GPTBot and as ClaudeBot; each must answer 200 with the page, not a
challenge. The sample: every serving zone that answers 200 on its own host, sorted by name, every k-th taken (k = count // 20). Usage: python -X utf8 -I crawl_proof.py <plan_site03.json> <wire.json> <out.json>"""
import json, sys, re, time, concurrent.futures as cf
import requests
P = json.load(open(sys.argv[1], encoding='utf-8')); W = {w['zone']: w for w in json.load(open(sys.argv[2], encoding='utf-8'))['zones']}
def serving(est): return sorted(p['zone'] for p in P if p['estate'] == est and (W.get(p['zone']) or {}).get('status') == 200 and ((W.get(p['zone']) or {}).get('final_host') or '').replace('www.', '') == p['zone'])
def sample(lst): k = max(1, len(lst) // 20); s = lst[::k][:20]; return s
S = {'allooloo': sample(serving('allooloo')), 'gsc': sample(serving('gsc'))}
UAS = {'GPTBot': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)', 'ClaudeBot': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)'}
CH = re.compile(r'Just a moment|cf-chl|challenge-platform|Attention Required|Enable JavaScript and cookies|cf_chl_opt', re.I)
def one(args):
    est, z, ua = args; o = {'zone': z, 'estate': est, 'ua': ua}
    try:
        r = requests.get(f'https://{z}/', headers={'User-Agent': UAS[ua], 'Accept': 'text/html,*/*'}, timeout=30, allow_redirects=True)
        o['status'] = r.status_code; o['bytes'] = len(r.content); o['challenge'] = bool(CH.search(r.text[:4000])) or r.headers.get('cf-mitigated') == 'challenge' or r.status_code in (403, 503)
        t = re.search(r'<title>(.*?)</title>', r.text, re.S | re.I); o['note'] = (t.group(1).strip()[:80] if t else '') + (' · cf-mitigated=' + r.headers['cf-mitigated'] if r.headers.get('cf-mitigated') else '')
        o['ok'] = r.status_code == 200 and not o['challenge']
    except Exception as e: o.update(status='error', challenge=False, note=repr(e)[:80], ok=False)
    return o
jobs = [(est, z, ua) for est, zs in S.items() for z in zs for ua in UAS]
with cf.ThreadPoolExecutor(12) as ex: R = list(ex.map(one, jobs))
json.dump({'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'sample': S, 'rows': R}, open(sys.argv[3], 'w', encoding='utf-8'), indent=0)
for est in S: print(est, 'zones', len(S[est]), 'fetches', sum(1 for r in R if r['estate'] == est), 'ok', sum(1 for r in R if r['estate'] == est and r['ok']))
print('FAIL lines:'); [print(' ', r['estate'], r['zone'], r['ua'], r['status'], 'challenge' if r.get('challenge') else '', r.get('note', '')) for r in R if not r['ok']]
