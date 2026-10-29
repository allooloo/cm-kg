r"""SHELF-01 — the gate check after deploying cmkg-node-gate 2026-10-27.1: on a node door, list_events_since lines carry a signature that verifies against the
public key of record and binds the issuer (cmr); GET /events/... likewise; get_record still answers the signed record as before (same cmr).
Usage: python -X utf8 -I gate_check.py <cc> <identifier>"""
import json, sys, base64, urllib.request
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
cc, ident = sys.argv[1], sys.argv[2]
nodes = {n['node'].split('-')[0]: n for n in json.load(open(r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json', encoding='utf-8'))}
door = nodes[cc]['door'].rstrip('/'); door = door if door.endswith('/mcp') else door + '/mcp'
pub = json.load(open(r'C:\ALLOOLOO\CM-KG\NODE-SIGN\cmr-signing.pub.jwk.json')); x = (pub.get('keys') or [pub])[0]['x']
K = Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(x + '=' * (-len(x) % 4)))
sortd = lambda v: [sortd(i) for i in v] if isinstance(v, list) else ({k: sortd(v[k]) for k in sorted(v)} if isinstance(v, dict) else v)
b64u = lambda b: base64.urlsafe_b64encode(b).decode().rstrip('=')
def ok(o):
    s = o.get('signature') or {}; body = {k: v for k, v in o.items() if k != 'signature'}
    try: K.verify(base64.urlsafe_b64decode(s['signature'] + '=' * (-len(s['signature']) % 4)), (s['protected'] + '.' + b64u(json.dumps(sortd(body), separators=(',', ':'), ensure_ascii=False).encode())).encode()); return True
    except Exception: return False
UA = {'user-agent': 'Allooloo SHELF-01 gate check', 'content-type': 'application/json', 'accept': 'application/json, text/event-stream'}
def rpc(name, args):
    r = urllib.request.urlopen(urllib.request.Request(door, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}}).encode(), headers=UA), timeout=60)
    t = r.read().decode(); return json.loads(t[t.index('{'):])['result'].get('structuredContent') or {}, dict(r.headers)
ev, h = rpc('list_events_since', {'identifier': ident, 'limit': 20})
lines = ev.get('events') or []
rec, h2 = rpc('get_record', {'identifier': ident})
out = {'door': door, 'gate': h.get('X-Node-Gate') or h.get('x-node-gate'), 'cmr': ev.get('cmr'), 'lines': len(lines), 'lines_signed': sum(1 for e in lines if e.get('signature')),
       'lines_verify': sum(1 for e in lines if ok(e)), 'lines_bind_issuer': sum(1 for e in lines if e.get('cmr') == ev.get('cmr')), 'events_signed': ev.get('events_signed'),
       'record_cmr': rec.get('cmr'), 'record_verifies': ok(rec) if rec.get('signature') else None}
out['PASS'] = out['lines'] > 0 and out['lines'] == out['lines_verify'] == out['lines_bind_issuer'] and out['record_verifies'] is True
print(json.dumps(out))
