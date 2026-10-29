r"""ZONES-02 — the one scheduled later check of DNSSEC on the 17 zones (no polling). DNSSEC was enabled 2026-10-26 and the DS issued; the registrar is
Cloudflare Registrar, which publishes the DS itself. Reads Cloudflare's DNSSEC status and the DS at the parent (DoH), writes AZURE\dnssec-z2-<UTC stamp>.txt/.json.
Token in-process, never printed. Run once by the Task Scheduler task 'Allooloo ZONES-02 DNSSEC check' (one-time trigger)."""
import json, sys, datetime, urllib.request
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\zones-do5')
from cf import cf, zones
ZONES = ('data-now.ai data-vintage.ai data-ark.ai hunter-agent.ai hedge-agent.ai ark-agent.ai data-record.ai data-eco.ai data-rco.ai '
         'data-now.com data-now.io data-now.org data-vintage.com data-vintage.io data-vintage.org data-ark.io data-live.ai data-ark.org hedge-agent.com').split()   # + the ZONES-02 tail two
def doh(name, typ):
    try:
        with urllib.request.urlopen(urllib.request.Request(f'https://cloudflare-dns.com/dns-query?name={name}&type={typ}&do=1', headers={'accept': 'application/dns-json'}), timeout=30) as x: return json.loads(x.read())
    except Exception as e: return {'error': str(e)[:100]}
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%MZ'); out = {}; lines = []
for n in ZONES:
    z = zones(n)[0]; st = (cf('GET', f"/zones/{z['id']}/dnssec").get('result') or {}).get('status'); ds = doh(n, 'DS'); k = len([a for a in ds.get('Answer', []) if a.get('type') == 43])
    out[n] = {'cloudflare': st, 'ds_at_parent': k, 'ad': ds.get('AD')}; lines.append(f"{n}: cloudflare={st} ds_at_parent={k} -> {'LANDED' if st == 'active' and k else 'not yet'}")
base = rf'C:\ALLOOLOO\AZURE\dnssec-z2-{stamp}'
json.dump(out, open(base + '.json', 'w'), indent=1); open(base + '.txt', 'w', encoding='utf-8').write('\n'.join(lines) + f"\nlanded {sum(1 for l in lines if l.endswith('LANDED'))} of {len(lines)}\n")
print(open(base + '.txt', encoding='utf-8').read())
