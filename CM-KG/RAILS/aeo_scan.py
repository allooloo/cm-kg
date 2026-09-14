r"""START_ME_UP_5 §7.1/§7.3 — scan every surface in scope on isitagentready.com (POST /api/scan) and keep the per-check JSON.
Usage: python aeo_scan.py <label> [host ...]   -> AZURE\aeo-scan-<date>-<label>\<host>.json + summary.tsv (check-level table, pass/neutral/fail counts).
Transport is curl with a browser-shaped User-Agent: the scanner's edge refuses Python's own client signature (Cloudflare 1010).
Spacing between scans is 20 s; a 429 waits 60 s and retries once. No key. One pass, never a loop."""
import json, sys, time, os, datetime, subprocess
sys.stdout.reconfigure(encoding='utf-8')
NODES = ['ca', 'us', 'uk', 'fr', 'nl', 'ch', 'de', 'au', 'sg', 'jp', 'kr', 'hk']
PRODUCTS = ['trades', 'ask', 'coverage', 'esg', 'issuers', 'disclosure', 'registries', 'radar', 'x402']
SCOPE = ['allooloo.io'] + [f'agentic-{p}.ai' for p in PRODUCTS] + ['kyp-model.ai'] + [f'{cc}-cm-kg.ai' for cc in NODES]
label = sys.argv[1]; hosts = sys.argv[2:] or SCOPE
out = rf'C:\ALLOOLOO\AZURE\aeo-scan-{datetime.date.today()}-{label}'; os.makedirs(out, exist_ok=True)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Allooloo aeo rail'
def scan(h):
    for attempt in (1, 2):
        r = subprocess.run(['curl', '-s', '-m', '240', '-A', UA, '-H', 'content-type: application/json', '-H', 'accept: application/json', '-X', 'POST', 'https://isitagentready.com/api/scan', '-d', json.dumps({'url': f'https://{h}'}), '-w', '\n%{http_code}'], capture_output=True, text=True, encoding='utf-8', errors='replace')
        body, _, code = r.stdout.rpartition('\n')
        if code == '429' and attempt == 1: time.sleep(60); continue
        if code != '200': return {'error': f'HTTP {code}', 'body': body[:300]}
        try: return json.loads(body)
        except Exception as e: return {'error': 'bad json ' + str(e)[:80], 'body': body[:300]}
rows = []; order = None
for i, h in enumerate(hosts):
    if i: time.sleep(20)
    d = scan(h); json.dump(d, open(os.path.join(out, h + '.json'), 'w'), indent=1)
    if 'checks' not in d: rows.append((h, {'error': d.get('error')})); print(h, 'ERROR', d.get('error'), flush=True); continue
    st = {}
    for cat, c in d['checks'].items():
        for k, v in c.items(): st[k] = v['status']
    order = order or list(st); rows.append((h, st))
    n = lambda s: sum(1 for x in st.values() if x == s)
    print(f"{h:22s} L{d.get('level')} pass {n('pass'):2d} · neutral {n('neutral')} · fail {n('fail')} · commerce={d.get('isCommerce')} · fails: {', '.join(k for k, v in st.items() if v == 'fail') or 'none'}", flush=True)
lines = ['host\t' + '\t'.join(order or [])]
for h, st in rows: lines.append(h + '\t' + '\t'.join(st.get(k, '?') for k in (order or [])))
open(os.path.join(out, 'summary.tsv'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('written', out)
