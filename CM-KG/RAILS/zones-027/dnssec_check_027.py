r"""ORDER-027 B1 — the one scheduled later check of DNSSEC on the 38 product-door zones (no polling). DNSSEC was enabled 2026-10-17; the DS
lands on the registrar's clock. Reads Cloudflare's DNSSEC status and the DS at the parent (DoH), writes AZURE\dnssec-027-<UTC stamp>.txt/.json.
Token in-process, never printed. Run once by the Task Scheduler task 'Allooloo ORDER-027 DNSSEC check' (one-time trigger)."""
import json, sys, datetime, urllib.request
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\zones-027')
from zones027 import cf, zone, rows
def doh(name, typ):
    try:
        with urllib.request.urlopen(urllib.request.Request(f'https://cloudflare-dns.com/dns-query?name={name}&type={typ}&do=1', headers={'accept': 'application/dns-json'}), timeout=30) as x: return json.loads(x.read())
    except Exception as e: return {'error': str(e)[:100]}
stamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H%MZ'); out = {}; lines = []
for r in rows():
    z = zone(r['zone'])
    if not z: out[r['zone']] = 'not in account'; lines.append(f"{r['zone']}: not in account (not registered at 2026-10-17)"); continue
    st = (cf('GET', f"/zones/{z['id']}/dnssec").get('result') or {}).get('status'); ds = doh(r['zone'], 'DS'); n = len([a for a in ds.get('Answer', []) if a.get('type') == 43])
    out[r['zone']] = {'cloudflare': st, 'ds_at_parent': n, 'ad': ds.get('AD')}; lines.append(f"{r['zone']}: cloudflare={st} ds_at_parent={n} -> {'LANDED' if st == 'active' and n else 'not yet'}")
base = rf'C:\ALLOOLOO\AZURE\dnssec-027-{stamp}'
json.dump(out, open(base + '.json', 'w'), indent=1); open(base + '.txt', 'w', encoding='utf-8').write('\n'.join(lines) + f"\nlanded {sum(1 for l in lines if l.endswith('LANDED'))} of {len(lines)}\n")
