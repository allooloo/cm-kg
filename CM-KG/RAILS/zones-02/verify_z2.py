r"""verify_z2.py — ZONES-02 close read, live: the nine pages and their kit paths, the eight forwards (+ www), robots open to AI crawlers, pay line, price line,
copy fence (no 'product'/'division' beside Data Now / Vintage / Ark), no script. Usage: python -X utf8 -I verify_z2.py -> verify-z2-<UTC stamp>.json"""
import json, re, os, datetime, urllib.request, urllib.error
PAGES = ['data-now.ai', 'data-vintage.ai', 'data-ark.ai', 'hunter-agent.ai', 'hedge-agent.ai', 'ark-agent.ai', 'data-record.ai', 'data-eco.ai', 'data-rco.ai']
FWD = {'data-now.com': 'data-now.ai', 'data-now.io': 'data-now.ai', 'data-now.org': 'data-now.ai', 'data-live.ai': 'data-now.ai', 'data-vintage.com': 'data-vintage.ai', 'data-vintage.io': 'data-vintage.ai', 'data-vintage.org': 'data-vintage.ai', 'data-ark.io': 'data-ark.ai', 'data-ark.org': 'data-ark.ai', 'hedge-agent.com': 'hedge-agent.ai'}   # + the ZONES-02 tail two
KIT = ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt']
class NR(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
op = urllib.request.build_opener(NR)
def get(u):
    try: r = op.open(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (Allooloo ZONES-02 verify)'}), timeout=30); return r.status, r.headers.get('location'), r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e: return e.code, e.headers.get('location'), ''
    except Exception as e: return 0, None, str(e)[:120]
out = {'pages': {}, 'forwards': {}}; bad = 0
for h in PAGES:
    st, _, b = get(f'https://{h}/'); kit = {p: get(f'https://{h}{p}')[0] for p in KIT}; wst, wloc, _ = get(f'https://www.{h}/a?b=1')
    rb = get(f'https://{h}/robots.txt')[2]
    row = {'page': st, 'kit_all_200': all(v == 200 for v in kit.values()), 'kit': kit, 'www': f'{wst} {wloc}', 'pay_line': '$0.01 a read, paid in the call on x402.' in b,
           'price_line': ('per market, per year — price to be set' in b) if h == 'data-vintage.ai' else None, 'script': bool(re.search(r'<script(?! type="application/ld\+json")', b)),
           'fence_hits': re.findall(r'Data (?:Now|Vintage|Ark)[^.<]{0,40}\b(?:product|division)s?\b', b, re.I), 'robots_blocks_ai': bool(re.search(r'(?im)^user-agent:\s*(gptbot|claudebot|ccbot|google-extended)[\s\S]{0,80}?^disallow:\s*/\s*$', rb))}
    ok = st == 200 and row['kit_all_200'] and row['pay_line'] and not row['script'] and not row['fence_hits'] and not row['robots_blocks_ai'] and wst == 301 and (row['price_line'] in (None, True))
    row['ok'] = ok; bad += 0 if ok else 1; out['pages'][h] = row
    print(f"{'OK ' if ok else 'BAD'} {h:16s} page={st} kit={'all 200' if row['kit_all_200'] else kit} www={row['www']} pay={row['pay_line']} price={row['price_line']} script={row['script']} fence={row['fence_hits']} robots_block_ai={row['robots_blocks_ai']}")
for h, t in FWD.items():
    for host in (h, 'www.' + h):
        st, loc, _ = get(f'https://{host}/x/y?q=1'); ok = st == 301 and loc == f'https://{t}/x/y?q=1'
        out['forwards'][host] = {'status': st, 'location': loc, 'ok': ok}; bad += 0 if ok else 1
        print(f"{'OK ' if ok else 'BAD'} {host:20s} {st} -> {loc}")
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%MZ'); out['bad'] = bad
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'verify-z2-{stamp}.json'), 'w'), indent=1); print('bad', bad)
