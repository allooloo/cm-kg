"""SITE-03 — the 301 check of every twin: GET https://<zone>/ without following, expect 301 and a Location on the target; then GET the target and expect 200.
Serve zones: expect 200 on their own host. Usage: python -X utf8 -I verify_site03.py <plan.json> <out.json>"""
import json, sys, time, concurrent.futures as cf, urllib.parse
import requests
P = [p for p in json.load(open(sys.argv[1], encoding='utf-8')) if p['estate'] in ('allooloo', 'allooloo-forward') and p['role'] in ('301', 'serve')]
UA = {'User-Agent': 'Allooloo SITE-03 close check'}
def norm(u): return (u or '').replace('http://', 'https://').replace('://www.', '://').rstrip('/')
def one(p):
    n = p['zone']; o = {'zone': n, 'role': p['role'], 'target': p['target']}
    try:
        r = requests.get(f'https://{n}/', headers=UA, timeout=30, allow_redirects=False); o['status'] = r.status_code; o['location'] = r.headers.get('location', '')
        if p['role'] == '301':
            want = p['target']; got = o['location']
            o['hop_ok'] = r.status_code in (301, 308) and norm(got).split('#')[0].startswith(norm(want).split('#')[0]) and (('#' not in want) or got.endswith(want.split('#')[1]) or ('#' + want.split('#')[1]) in got)
            try: t = requests.get(want, headers=UA, timeout=30, allow_redirects=True); o['target_status'] = t.status_code; o['target_final'] = t.url
            except Exception as e: o['target_status'] = 'error'; o['target_final'] = repr(e)[:80]
            o['ok'] = bool(o['hop_ok'] and o['target_status'] == 200)
        else:
            o['ok'] = r.status_code == 200
    except Exception as e: o.update(status='error', error=repr(e)[:100], ok=False)
    return o
with cf.ThreadPoolExecutor(16) as ex: R = list(ex.map(one, P))
json.dump({'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'zones': R}, open(sys.argv[2], 'w', encoding='utf-8'), indent=0)
from collections import Counter
t = [r for r in R if r['role'] == '301']; s = [r for r in R if r['role'] == 'serve']
print('301 zones', len(t), 'ok', sum(1 for r in t if r['ok']), '| serve zones', len(s), 'ok', sum(1 for r in s if r['ok']))
print('301 failures:'); [print(' ', r['zone'], r.get('status'), r.get('location', '')[:60], '→', r.get('target_status'), r.get('error', '')) for r in t if not r['ok']]
print('serve failures:'); [print(' ', r['zone'], r.get('status'), r.get('location', '')[:60], r.get('error', '')) for r in s if not r['ok']]
