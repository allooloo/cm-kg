r"""iw_patch.py — IW-MOVE-01 steps 1 and 5: the code as deployed (read out of the running images into extracted\) with the smallest change that lets the
Allooloo side sign under its own keys and stand beside the old side. Writes patched\<image>\…; every replacement must match the count given or the run
stops. Nothing else in any file changes.
  key ids     the two key ids are read from the environment (AMN_KID, AMN_X402_KID), default = the old ids: an image run without them behaves as before
  hosts       the Ops Agents' three door hosts are read from the environment (AMN_HUB, AMN_DOOR, AMN_BRAND), default = as before (the trial cycle points
              them at the twin's own door)
  keyring     /.well-known/jwks.json: the two NEW public keys first (they sign from now), the two OLD public keys kept, marked verification only
              /x402/jwks.json: the runtime key plus the old receipts key from x402-old-keys.json, so every receipt already written still verifies
  copy        the pages name the kid that signs now and say rows signed before the move carry the old kid
Usage: python -X utf8 -I iw_patch.py <new rows kid> <new rows x> <new x402 kid> <new x402 x> <date>"""
import json, os, shutil, sys, pathlib
H = pathlib.Path(__file__).parent; E = H / 'extracted'; P = H / 'patched'; KID, X, XKID, XX, DATE = sys.argv[1:6]
if P.exists(): shutil.rmtree(P)
def patch(src, dst, pairs):
    s = (E / src).read_text(encoding='utf-8')
    for o, n, k in pairs:
        if s.count(o) != k: sys.exit(f'STOP {src}: {s.count(o)} of {k} for {o[:70]!r}')
        s = s.replace(o, n)
    (P / dst).parent.mkdir(parents=True, exist_ok=True); (P / dst).write_text(s, encoding='utf-8', newline='\n'); print('patched', dst, len(pairs))
OLDK, OLDX = 'amn-2026-10', 'amn-x402-receipts-2026-10'
ENVK = "os.environ.get('AMN_KID', 'amn-2026-10')"; ENVX = "os.environ.get('AMN_X402_KID', 'amn-x402-receipts-2026-10')"
for v in ('ops-iw01', 'ops-nightly02', 'ops-fix'):
    patch(f'{v}/job/ops/amnlib.py', f'{v}/amnlib.py', [("KID = 'amn-2026-10'; X402_KID = 'amn-x402-receipts-2026-10'", f"KID = {ENVK}; X402_KID = {ENVX}   # IW-MOVE-01: the key ids of the side that signs", 1)])
    patch(f'{v}/job/ops/ledger.py', f'{v}/ledger.py', [("KID = 'amn-2026-10'\n", f"KID = {ENVK}   # IW-MOVE-01\n", 1)])
    patch(f'{v}/job/ops/job_amn.py', f'{v}/job_amn.py', [("DOOR = 'https://mcp.a2a-amn.ai'; HUB = 'https://a2a-amn.ai'; BRAND = 'https://agentmarketnews.ai'", "DOOR = os.environ.get('AMN_DOOR', 'https://mcp.a2a-amn.ai'); HUB = os.environ.get('AMN_HUB', 'https://a2a-amn.ai'); BRAND = os.environ.get('AMN_BRAND', 'https://agentmarketnews.ai')   # IW-MOVE-01", 1)])
    patch(f'{v}/job/ops/ark_amn.py', f'{v}/ark_amn.py', [("HUB = 'https://a2a-amn.ai'; DOOR = 'https://mcp.a2a-amn.ai'", "HUB = os.environ.get('AMN_HUB', 'https://a2a-amn.ai'); DOOR = os.environ.get('AMN_DOOR', 'https://mcp.a2a-amn.ai')   # IW-MOVE-01", 1)])
    patch(f'{v}/job/ops/verify_amn.py', f'{v}/verify_amn.py', [("HUB = 'https://a2a-amn.ai'; DOOR = 'https://mcp.a2a-amn.ai'", "HUB = os.environ.get('AMN_HUB', 'https://a2a-amn.ai'); DOOR = os.environ.get('AMN_DOOR', 'https://mcp.a2a-amn.ai')   # IW-MOVE-01", 1)])
D = 'door/app/'
patch(D + 'server.py', 'door/server.py', [("VERSION = '1.3.3'; KID = 'amn-2026-10';", f"VERSION = '1.3.3'; KID = {ENVK};", 1), ("Ed25519 against kid amn-2026-10; prev chains", "Ed25519 against the kid the event names (keyring /.well-known/jwks.json); prev chains", 1)])
patch(D + 'ledger.py', 'door/ledger.py', [("KID = 'amn-2026-10'\n", f"KID = {ENVK}   # IW-MOVE-01\n", 1)])
patch(D + 'x402.py', 'door/x402.py', [("KID = 'amn-x402-receipts-2026-10'; NETWORK", f"KID = {ENVX}; NETWORK", 1),
    # CEO 2026-11-12: receipts on the Allooloo side stamp issuer "allooloo" (AMN_RECEIPT_ISSUER); the old side's default stays as it was. The DUNS in the
    # old body is the old issuer's number, so it rides only with the old issuer string.
    ("'issuer': 'wefetch', 'duns': '24-336-6774'}", "'issuer': os.environ.get('AMN_RECEIPT_ISSUER', 'wefetch'), **({} if os.environ.get('AMN_RECEIPT_ISSUER') else {'duns': '24-336-6774'})}", 1),
    ("    return {'keys': [{'kty': 'OKP', 'crv': 'Ed25519', 'kid': KID, 'x': b64u(k), 'use': 'sig', 'alg': 'EdDSA'}]}",
     "    # IW-MOVE-01: the key that signs now, then the earlier receipts key(s), verification only (x402-old-keys.json beside this file), so every receipt already written still verifies\n"
     "    try: old = [o for o in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'x402-old-keys.json'), encoding='utf-8'))['keys'] if o.get('kid') != KID]\n"
     "    except Exception: old = []\n"
     "    return {'keys': [{'kty': 'OKP', 'crv': 'Ed25519', 'kid': KID, 'x': b64u(k), 'use': 'sig', 'alg': 'EdDSA'}] + old}", 1)])
NOTE_ROW = f'kid {KID}; a row signed before {DATE} carries kid {OLDK}'
for f, n in (('iw.py', None), ('pages.py', None)):
    s = (E / D / f).read_text(encoding='utf-8'); c1 = s.count('kid ' + OLDX); c0 = s.count('kid ' + OLDK)
    s = s.replace('kid ' + OLDX, f'kid {XKID}; a receipt issued before {DATE} carries kid {OLDX}').replace('kid ' + OLDK, NOTE_ROW)
    (P / 'door' / f).write_text(s, encoding='utf-8', newline='\n'); print('patched door/' + f, 'kid mentions', c0, 'receipt-kid mentions', c1)
j = json.loads((E / D / 'jwks.json').read_text(encoding='utf-8')); old = j['keys']
for k in old: k['note'] = f"verification only since {DATE}: " + k.get('note', '') + f" signed under this key until {DATE}"; k['status'] = 'verification only'
new = [{'kty': 'OKP', 'crv': 'Ed25519', 'x': X, 'kid': KID, 'alg': 'EdDSA', 'use': 'sig', 'note': f'signs from {DATE}: the record rows, the ledger events, the statements and the door', 'status': 'signing'},
       {'kty': 'OKP', 'crv': 'Ed25519', 'x': XX, 'kid': XKID, 'alg': 'EdDSA', 'use': 'sig', 'note': f'signs from {DATE}: the x402 settlement receipts', 'status': 'signing'}]
j['operator'] = 'Allooloo Technologies Corp.'; j['keys'] = new + old; j['note'] = f"Issuerwire keyring: {KID} signs every record row, ledger event, weekly statement and door answer from {DATE}; {XKID} signs x402 settlement receipts from {DATE}. {OLDK} and {OLDX} signed before that date and stay published for verification only. The private keys are held in Key Vault, never in any repo."
(P / 'door' / 'jwks.json').write_text(json.dumps(j, indent=1), encoding='utf-8', newline='\n')
(P / 'door' / 'x402-old-keys.json').write_text(json.dumps({'keys': [{'kty': 'OKP', 'crv': 'Ed25519', 'kid': OLDX, 'x': next(k['x'] for k in old if k['kid'] == OLDX), 'use': 'sig', 'alg': 'EdDSA', 'status': 'verification only'}]}, indent=1), encoding='utf-8', newline='\n')
print('keyring: keys', [k['kid'] for k in j['keys']])
