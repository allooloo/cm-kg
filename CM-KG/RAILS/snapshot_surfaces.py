"""ORDER-020 §0.1 — the page is a record: prior renders go to the pond. Fetches every surface (HTML + llms.txt + facts.json) and writes them under
CM-KG\POND\estate\surfaces\<yyyy-mm-dd>[-n]\<host>\ as an immutable dated drop (new beside old, never on top). A reader can see what a page said on any date.
Usage: python snapshot_surfaces.py [cc ...]   (no args: every surface — 12 nodes, 8 products, allooloo.io and its record pages, the roots)."""
import os, sys, datetime, requests
ROOT = r'C:\ALLOOLOO\CM-KG\POND\estate\surfaces'
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__))); import roster   # ENUM-01 (DAY ORDER 6): the roster of record
NODES = roster.codes()   # ENUM-01: every roster node's surfaces (the twelve were typed here)
PRODUCTS = ['trades', 'ask', 'coverage', 'esg', 'issuers', 'disclosure', 'registries', 'radar', 'x402']
def hosts(args):
    if args: return [f'{cc}-cm-kg.ai' for cc in args]
    return [f'{cc}-cm-kg.ai' for cc in NODES] + [f'agentic-{p}.ai' for p in PRODUCTS] + ['allooloo.io', 'kyp-model.ai', 'capitalmarketsknowledgegraph.ai', 'cm-record.org'] + [f'{cc}-issuer.ai' for cc in NODES] + ['kyp-model.org', 'issuerwire.org']   # ORDER-034 (2026-10-22): sovereign node pages + standards
PATHS = {'allooloo.io': ['/', '/support', '/setup', '/status', '/terms', '/privacy', '/security', '/no-cookies', '/llms.txt', '/facts.json', '/status.json'], 'capitalmarketsknowledgegraph.ai': ['/', '/docs', '/llms.txt', '/facts.json'], 'agentic-radar.ai': ['/', '/radar.json', '/llms.txt', '/facts.json'], 'agentic-x402.ai': ['/', '/api', '/x402/jwks.json', '/llms.txt', '/facts.json', '/.well-known/agent-card.json']}
day = datetime.date.today().isoformat(); d = os.path.join(ROOT, day); n = 1
while os.path.exists(d): n += 1; d = os.path.join(ROOT, f'{day}-{n}')
os.makedirs(d); count = 0
for h in hosts(sys.argv[1:]):
    for p in PATHS.get(h, ['/', '/llms.txt', '/facts.json']):
        try:
            r = requests.get(f'https://{h}{p}', timeout=60, headers={'User-Agent': 'Allooloo snapshot rail'})
            fn = 'index.html' if p == '/' else p.strip('/').replace('/', '_')
            if p == '/' or fn in ('status', 'terms', 'privacy', 'security', 'no-cookies'): fn = (fn if fn != 'index.html' else 'index') + '.html'
            os.makedirs(os.path.join(d, h), exist_ok=True); open(os.path.join(d, h, fn), 'wb').write(r.content); count += 1
        except Exception as e: print('miss', h, p, e)
open(os.path.join(d, 'MANIFEST.txt'), 'w', encoding='utf-8').write(f'surfaces snapshot {day} · {count} files · sources: the live hosts over HTTPS · X-Surface-Version as served\n')
print('snapshot', d, count, 'files')
