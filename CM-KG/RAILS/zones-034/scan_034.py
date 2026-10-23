"""ORDER-034 — the agent-readiness grade of every ORDER-034 zone from the instrument of record (isitagentready.com POST /api/scan). Read-only; writes zones-034\\scan-<stamp>.json."""
import json, os, datetime, urllib.request, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__)); STAMP = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
ZONES = [f'{c}-issuer.ai' for c in 'ca uk us de fr nl ch au sg jp kr hk'.split()] + ['kyp-model.org', 'issuerwire.org']
def scan(h):
    try:
        r = urllib.request.urlopen(urllib.request.Request('https://isitagentready.com/api/scan', data=json.dumps({'url': 'https://' + h}).encode(), headers={'Content-Type': 'application/json', 'User-Agent': 'curl/8.0'}), timeout=180)
        d = json.load(r); checks = d.get('checks') or {}
        res = [(f'{cat}.{k}', v.get('status')) for cat, cc in checks.items() if isinstance(cc, dict) for k, v in cc.items() if isinstance(v, dict)]
        return h, {'level': d.get('level'), 'passed': sum(1 for _, s in res if s == 'pass'), 'scored': sum(1 for _, s in res if s in ('pass', 'fail')), 'fails': [n for n, s in res if s == 'fail']}
    except Exception as e: return h, {'error': repr(e)[:200]}
with cf.ThreadPoolExecutor(5) as ex: out = dict(ex.map(scan, ZONES))
json.dump({'read_at': STAMP, 'instrument': 'isitagentready.com POST /api/scan', 'zones': out}, open(os.path.join(HERE, f'scan-{STAMP}.json'), 'x', encoding='utf-8'), indent=1)
for h, r in out.items(): print(h, r)
