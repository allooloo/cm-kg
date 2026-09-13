"""One-off DNSSEC landing check (TO 100 item 2 — scheduled later, no polling). For each of the 22 served zones: Cloudflare DNSSEC status, DS at the parent
(DoH 1.1.1.1, type DS), and whether a validating resolver sets AD on the zone's _index._agents TXT (DNS-AID needs DNSSEC-validated answers).
Writes AZURE\\dnssec-check-<UTC stamp>.json and a one-line-per-zone .txt beside it. Token in-process, never printed."""
import json, urllib.request, datetime, os, sys
sys.stdout.reconfigure(encoding='utf-8')
TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0].strip()
if '=' in TOK and ' ' not in TOK.split('=')[0]: TOK = TOK.split('=', 1)[1].strip()
H = {'authorization': 'Bearer ' + TOK, 'content-type': 'application/json'}
def cf(path):
    r = urllib.request.Request('https://api.cloudflare.com/client/v4' + path, headers=H)
    try:
        with urllib.request.urlopen(r, timeout=60) as x: return json.loads(x.read())
    except Exception as e: return {'errors': str(e)[:120]}
def doh(name, typ):
    r = urllib.request.Request(f'https://cloudflare-dns.com/dns-query?name={name}&type={typ}&do=1', headers={'accept': 'application/dns-json'})
    try:
        with urllib.request.urlopen(r, timeout=30) as x: return json.loads(x.read())
    except Exception as e: return {'error': str(e)[:120]}
ZONES = ['allooloo.io', 'kyp-model.ai'] + [f'agentic-{p}.ai' for p in ['trades', 'ask', 'coverage', 'esg', 'issuers', 'disclosure', 'registries', 'radar', 'x402']] + [f'{cc}-cm-kg.ai' for cc in ['ca', 'uk', 'us', 'de', 'fr', 'nl', 'ch', 'au', 'sg', 'jp', 'kr', 'hk']]
stamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H%MZ'); out = {}; lines = []
for z in ZONES:
    j = cf(f'/zones?name={z}'); zid = j['result'][0]['id'] if j.get('result') else None
    st = (cf(f'/zones/{zid}/dnssec').get('result') or {}).get('status') if zid else None
    ds = doh(z, 'DS'); ad = doh(f'_index._agents.{z}', 'TXT')
    n_ds = len([a for a in ds.get('Answer', []) if a.get('type') == 43])
    out[z] = {'cloudflare_dnssec': st, 'ds_at_parent': n_ds, 'ds_ad': ds.get('AD'), 'index_txt_answers': len(ad.get('Answer', [])), 'index_txt_ad': ad.get('AD'), 'checked_utc': stamp}
    ok = st == 'success' and n_ds > 0 and ad.get('AD') is True
    lines.append(f"{z}: cloudflare={st} ds_at_parent={n_ds} validated={ad.get('AD')} -> {'LANDED' if ok else 'not yet'}")
base = rf'C:\ALLOOLOO\AZURE\dnssec-check-{stamp}'
json.dump(out, open(base + '.json', 'w'), indent=1); open(base + '.txt', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('\n'.join(lines)); print('landed', sum(1 for l in lines if l.endswith('LANDED')), 'of', len(ZONES))
