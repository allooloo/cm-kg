r"""infra_policy.py — ENUM-01 (c) (DAY ORDER 6, 2026-10-25): what the standby, swap and boot-check rails need per market, read — never typed here.
  ark_region(cc)   the ark region policy line of record (RAILS\job\provision_jobs.py ARK, read from its source); none = the rail stops, named
  cf_zone_id(cc)   the Cloudflare zone of the node's public door (its roster entry's `door`: <cc>-cm-kg.ai, or eu-cm-kg.ai for a door under it), looked up by name
  ident(cc)        the market's example issuer from its roster entry (ECO examples.json on the roster), for the swap read-back
The roster is RAILS\zones-032\roster.py (identical copy of RAILS\job\roster.py, the pond rule)."""
import os, sys, json, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import roster
def _ark():
    src = open(os.path.join(HERE, '..', 'job', 'provision_jobs.py'), encoding='utf-8').read(); seg = src[src.index("NODES = {'nl'"):src.index('# ENUM-01 (DAY ORDER 6, 2026-10-25): region / ark')]
    ns = {}; exec(seg, ns); return ns['ARK']
ARK = _ark()
def ark_region(cc):
    if cc not in ARK: raise SystemExit(f'ROSTER POLICY GAP · ark region (provision_jobs ARK) · no line for: {cc} — rail refused')
    return ARK[cc]
def zone_of(cc):
    e = roster.entry(cc)
    if not e: raise SystemExit(f'ROSTER GAP · {cc} is not on the roster of record — rail refused')
    host = str(e.get('door') or '').split('://')[-1].rstrip('/')
    return 'eu-cm-kg.ai' if host.endswith('.eu-cm-kg.ai') else f'{cc}-cm-kg.ai'
def cf_zone_id(cc):
    tok = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip()
    r = json.load(urllib.request.urlopen(urllib.request.Request(f'https://api.cloudflare.com/client/v4/zones?name={zone_of(cc)}', headers={'Authorization': 'Bearer ' + tok}), timeout=30))
    if not r.get('result'): raise SystemExit(f'ROSTER GAP · no Cloudflare zone {zone_of(cc)} for {cc} — rail refused')
    return r['result'][0]['id']
def ident(cc):
    ex = (roster.entry(cc) or {}).get('example') or {}
    return (ex.get('ticker') or ex.get('isin') or '').split(':')[-1] or None
class Lazy(dict):
    def __init__(self, f): super().__init__(); self.f = f
    def __missing__(self, k): v = self.f(k); self[k] = v; return v
