r"""ORDER-032 C.4 — the one scheduled later check of DNSSEC on the five agent-swap zones (no polling). DNSSEC was enabled 2026-10-18 (status pending);
the DS lands on the registrar's clock. Reads Cloudflare's DNSSEC status, the DS record Cloudflare asks for, and the DS at the parent (DoH); writes
AZURE\dnssec-032-<UTC stamp>.txt/.json. Token in-process, never printed. Run once by the task 'Allooloo ORDER-032 DNSSEC check' (one-time trigger)."""
import json, sys, datetime, urllib.request
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\zones-032')
from zones032 import cf, zone, ZONES
def doh(name, typ):
    try:
        with urllib.request.urlopen(urllib.request.Request(f'https://cloudflare-dns.com/dns-query?name={name}&type={typ}&do=1', headers={'accept': 'application/dns-json'}), timeout=30) as x: return json.loads(x.read())
    except Exception as e: return {'error': str(e)[:100]}
stamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H%MZ'); out = {}; lines = []
for n in ZONES:
    z = zone(n)
    if not z: lines.append(f'{n}: NOT IN ACCOUNT'); continue
    d = cf('GET', f"/zones/{z['id']}/dnssec").get('result') or {}; ds = doh(n, 'DS'); parent = [a.get('data') for a in ds.get('Answer', []) if a.get('type') == 43]
    out[n] = {'cloudflare_status': d.get('status'), 'ds_wanted': d.get('ds'), 'ds_at_parent': parent, 'ad': ds.get('AD')}
    lines.append(f"{n}: cloudflare {d.get('status')} · DS at parent {'yes' if parent else 'no'} · validated (AD) {ds.get('AD')}" + ('' if parent else f" · DS to add at the registrar: {d.get('ds')}"))
base = rf'C:\ALLOOLOO\AZURE\dnssec-032-{stamp}'
json.dump(out, open(base + '.json', 'w'), indent=1); open(base + '.txt', 'w', encoding='utf-8').write('\n'.join(lines) + f"\nlanded {sum(1 for v in out.values() if v.get('ds_at_parent'))} of {len(ZONES)}\n")
print('\n'.join(lines))
