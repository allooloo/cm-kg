r"""ORDER-027 Part B: the 39 zones of Allooloo_New_Zones_2026-10-16.xlsx (ZONES tab is the row set). Shared helpers + read step.
Token in-process from AGENT KEYS\cloudflare.txt, never printed."""
import json, os, sys, urllib.request, urllib.error, openpyxl
sys.stdout.reconfigure(encoding='utf-8')
ACCT = 'dd2832b36f171b815f84c8487aada36b'
def tok(name='cloudflare.txt'):
    t = open(rf'C:\ALLOOLOO\AGENT KEYS\{name}', encoding='utf-8').read().strip().splitlines()[0].strip()
    return t.split('=', 1)[1].strip() if '=' in t and ' ' not in t.split('=')[0] else t
TOK = tok()
def cf(method, path, body=None, t=None):
    req = urllib.request.Request('https://api.cloudflare.com/client/v4' + path, data=json.dumps(body).encode() if body is not None else None, method=method, headers={'Authorization': 'Bearer ' + (t or TOK), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read())
        except Exception: return {'success': False, 'errors': [{'code': e.code}]}
def rows():
    ws = openpyxl.load_workbook(r'C:\ALLOOLOO\START_ME_UP\Allooloo_New_Zones_2026-10-16.xlsx', data_only=True)['ZONES']
    it = ws.iter_rows(values_only=True); hdr = next(it)
    return [dict(zip(hdr, r)) for r in it if r and r[0]]
def zone(name):
    j = cf('GET', f'/zones?name={name}&account.id={ACCT}'); return (j.get('result') or [None])[0]
if __name__ == '__main__':
    R = rows(); print(len(R), 'rows')
    for r in R:
        z = zone(r['zone'])
        if not z: print(f"{r['zone']:20s} NOT IN ACCOUNT"); continue
        ds = (cf('GET', f"/zones/{z['id']}/dnssec").get('result') or {}).get('status')
        bm = cf('GET', f"/zones/{z['id']}/bot_management"); bmr = bm.get('result') or {}
        ssl = (cf('GET', f"/zones/{z['id']}/settings/ssl").get('result') or {}).get('value')
        dns = cf('GET', f"/zones/{z['id']}/dns_records?per_page=100").get('result') or []
        print(f"{r['zone']:20s} {z['status']:8s} plan={z['plan']['legacy_id']:5s} ns={','.join(n.split('.')[0] for n in z['name_servers'])} dnssec={ds} ssl={ssl} ai_bots={bmr.get('ai_bots_protection')} fight={bmr.get('fight_mode')} crawler={bmr.get('crawler_protection')} robots={bmr.get('is_robots_txt_managed')} bm_err={(bm.get('errors') or [{}])[0].get('code') if not bm.get('success') else ''} dns={len(dns)} {[d['type']+':'+d['name'].split('.')[0] for d in dns][:6]}")
