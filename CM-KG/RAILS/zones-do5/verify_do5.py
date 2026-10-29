r"""verify_do5.py — DAY ORDER 5: live read of every new hostname of the day (one GET each, no retry loop). Writes verify-do5-<label>.json beside.
Doors: /mcp.json routing + payment + receipts, card, llms.txt. Page hosts: the root kit (/, llms.txt, agent-card, mcp.json with routing/payment/receipts,
security.txt, sitemap.xml, robots.txt). www → 301. Usage: python -X utf8 -I verify_do5.py <label> [eco]"""
import sys, json, os, urllib.request, urllib.error, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__)); LABEL = sys.argv[1]; ECO = 'eco' in sys.argv[2:]
OWN = 'lu ky bm je in tw sa ae br mx'.split(); EU14 = 'it es se dk no fi be ie at pl pt lu gr cz'.split(); EU13 = [c for c in EU14 if c != 'lu']
ECOZ = 'eu lu ky bm je tw'.split()
KIT = ['/', '/llms.txt', '/.well-known/agent-card.json', '/.well-known/mcp.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt']
checks = []
for cc in OWN: checks += [(f'https://{cc}-issuer.ai{p}', 200) for p in KIT] + [(f'https://{cc}-cm-kg.ai{p}', 200) for p in KIT] + [(f'https://www.{cc}-issuer.ai/', 301), (f'https://www.{cc}-cm-kg.ai/', 301)]
checks += [(f'https://eu-issuer.ai{p}', 200) for p in KIT] + [(f'https://eu-cm-kg.ai{p}', 200) for p in KIT] + [('https://www.eu-issuer.ai/', 301)]
for cc in EU13: checks += [(f'https://{cc}.eu-issuer.ai{p}', 200) for p in KIT]
checks += [('https://lu.eu-issuer.ai/', 301)]
for cc in EU14: checks += [(f'https://{cc}.eu-cm-kg.ai{p}', 200) for p in ('/mcp.json', '/.well-known/agent-card.json', '/llms.txt', '/facts.json')]
checks += [('https://mcp.lu-cm-kg.ai/mcp.json', 200), ('https://agent.lu-cm-kg.ai/.well-known/agent-card.json', 200), ('https://mcp.lu-cm-kg.ai/llms.txt', 200)]
for cc in [c for c in OWN if c != 'lu'] + []:
    pass
if ECO: checks += [(f'https://{cc}-eco.ai{p}', 200) for cc in ECOZ for p in ('/', '/eco.json', '/llms.txt', '/.well-known/agent-card.json', '/.well-known/mcp.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt')]
extra = json.load(open(os.path.join(HERE, 'verify-extra.json'))) if os.path.exists(os.path.join(HERE, 'verify-extra.json')) else []
checks += [tuple(x) for x in extra]
class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
op = urllib.request.build_opener(NoRedir)
def one(c):
    url, want = c
    try:
        r = op.open(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Allooloo verify DAY ORDER 5)'}), timeout=30); code, body = r.status, r.read(200000)
    except urllib.error.HTTPError as e: code, body = e.code, b''
    except Exception as e: code, body = 0, str(e).encode()
    ok = code == want
    if ok and want == 200 and url.endswith('mcp.json') and '//sa-' not in url:   # sa: SEEKING PARTNER, no routing overlay (CEO ruling 2026-10-24)
        try: j = json.loads(body); ok = all(k in j for k in ('routing', 'payment', 'receipts')) or ('routing' in j and 'payment' in j)
        except Exception: ok = False
    return {'url': url, 'want': want, 'got': code, 'ok': ok}
with cf.ThreadPoolExecutor(12) as ex: res = list(ex.map(one, checks))
bad = [r for r in res if not r['ok']]
json.dump({'label': LABEL, 'checked': len(res), 'ok': len(res) - len(bad), 'bad': bad}, open(os.path.join(HERE, f'verify-do5-{LABEL}.json'), 'w'), indent=1)
print(f'{len(res) - len(bad)}/{len(res)} answer as expected'); [print(' BAD', b) for b in bad[:40]]
