r"""SHELF-01 proof (Timeline): through the public market door, get_timeline's line count equals the record's event count, and every line's signature
verifies against the public key of record and binds the issuer. Usage: python -X utf8 -I proof_timeline.py <cc>:<identifier> [...]"""
import json, sys, os, base64, urllib.request
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
HERE = os.path.dirname(os.path.abspath(__file__))
nodes = {n['node'].split('-')[0]: n for n in json.load(open(r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json', encoding='utf-8'))}
pub = json.load(open(os.path.join(HERE, 'cmr-signing.pub.jwk.json'))); x = (pub.get('keys') or [pub])[0]['x']
K = Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(x + '=' * (-len(x) % 4)))
sortd = lambda v: [sortd(i) for i in v] if isinstance(v, list) else ({k: sortd(v[k]) for k in sorted(v)} if isinstance(v, dict) else v)
b64u = lambda b: base64.urlsafe_b64encode(b).decode().rstrip('=')
def ok(o):
    s = o.get('signature') or {}; body = {k: v for k, v in o.items() if k != 'signature'}
    try: K.verify(base64.urlsafe_b64decode(s['signature'] + '=' * (-len(s['signature']) % 4)), (s['protected'] + '.' + b64u(json.dumps(sortd(body), separators=(',', ':'), ensure_ascii=False).encode())).encode()); return True
    except Exception: return False
out = []
for arg in sys.argv[1:]:
    cc, ident = arg.split(':', 1); d = nodes[cc]['door'].rstrip('/'); d = d if d.endswith('/mcp') else d + '/mcp'
    def rpc(name, a):
        r = urllib.request.urlopen(urllib.request.Request(d, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': a}}).encode(), headers={'content-type': 'application/json', 'accept': 'application/json, text/event-stream', 'user-agent': 'Allooloo SHELF-01 proof'}), timeout=90)
        t = r.read().decode(); return json.loads(t[t.index('{'):])['result'].get('structuredContent') or {}
    tl = rpc('get_timeline', {'identifier': ident}); ev = tl.get('events') or []
    row = {'issuer': f'{cc}:{ident}', 'cmr': tl.get('cmr'), 'timeline_lines': len(ev), 'record_event_count': tl.get('record_event_count'), 'signed_and_verify': sum(1 for e in ev if ok(e)),
           'bind_issuer': sum(1 for e in ev if e.get('cmr') == tl.get('cmr')), 'oldest': (ev[0] or {}).get('date') if ev else None, 'newest': (ev[-1] or {}).get('date') if ev else None}
    row['PASS'] = row['timeline_lines'] == row['record_event_count'] == row['signed_and_verify'] == row['bind_issuer'] and row['timeline_lines'] > 0
    out.append(row); print(json.dumps(row))
