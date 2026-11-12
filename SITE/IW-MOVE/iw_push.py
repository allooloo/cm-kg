r"""iw_push.py — IW-MOVE-01 step 9: Issuerwire's code as it now runs, pushed to github.com/allooloo ONLY. Before each push the remote is read and must be
exactly the allooloo repository named here; anything else stops the run.
  door   C:\A2AAMN\GITHUB\a2a-amn (origin = allooloo/issuerwire-door): DOOR\ gets the files of the door image now serving (the deployed files + the key
         change): server.py ledger.py x402.py iw.py pages.py jwks.json x402-old-keys.json, and amncopy.py as deployed.
  ops    C:\A2AAMN\GITHUB\agentmarketnews (origin = allooloo/issuerwire): RAILS\ops\ gets the newest Ops Agents build as it runs (fix-20261103 + the key change).
  move   C:\ALLOOLOO (origin = allooloo/cm-kg): the move's own rails (SITE\IW-MOVE\*.py).
A .pre-iwmove01-2026-11-12 copy is left beside every file replaced (untracked). Every staged file is scanned for key shapes first (public_scan.py's
patterns); a hit stops the run. Usage: python -X utf8 -I iw_push.py plan|commit"""
import os, pathlib, re, shutil, subprocess, sys
H = pathlib.Path(__file__).parent; MODE = sys.argv[1]; GH = dict(os.environ, GH_CONFIG_DIR=r'C:\ALLOOLOO\.gh')
ps = open(r'C:\ALLOOLOO\CM-KG\RAILS\job\public_scan.py', encoding='utf-8').read(); PAT = eval(ps[ps.index('PAT = ') + 6: ps.index('}\n', ps.index('PAT = ')) + 1])
MSG = ("IW-MOVE-01 (2026-11-12): Issuerwire on the Allooloo subscription — new signing keys, the old keys kept for verification\n\n"
       "The key ids are read from the environment (AMN_KID, AMN_X402_KID; default = the earlier ids). The keyring lists iw-2026-11 and iw-x402-receipts-2026-11 as signing and keeps amn-2026-10 and "
       "amn-x402-receipts-2026-10 published, verification only; /x402/jwks.json serves the runtime key plus the earlier receipts key. Receipts stamp the issuer from AMN_RECEIPT_ISSUER. "
       "The Ops Agents' door hosts are read from the environment.\n\nCo-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\n")
def git(root, *a):
    r = subprocess.run(['git', '-c', 'core.quotepath=false', *a], cwd=root, capture_output=True, text=True, encoding='utf-8', errors='replace', env=GH); return r.returncode, (r.stdout or '').strip(), (r.stderr or '').strip()
def place(src, dst):
    dst = pathlib.Path(dst)
    if dst.exists() and dst.read_bytes().replace(b'\r\n', b'\n') == pathlib.Path(src).read_bytes().replace(b'\r\n', b'\n'): return False
    if dst.exists() and MODE == 'commit': shutil.copy2(dst, str(dst) + '.pre-iwmove01-2026-11-12')
    if MODE == 'commit': shutil.copy2(src, dst)
    return True
SETS = [
 (r'C:\A2AAMN\GITHUB\a2a-amn', 'https://github.com/allooloo/issuerwire-door.git', [(H / 'patched' / 'door' / f, 'DOOR/' + f) for f in ('server.py', 'ledger.py', 'x402.py', 'iw.py', 'pages.py', 'jwks.json', 'x402-old-keys.json')] + [(H / 'extracted' / 'door' / 'app' / 'amncopy.py', 'DOOR/amncopy.py')]),
 (r'C:\A2AAMN\GITHUB\agentmarketnews', 'https://github.com/allooloo/issuerwire.git', [(H / 'patched' / 'ops-fix' / f, 'RAILS/ops/' + f) for f in ('amnlib.py', 'ledger.py', 'job_amn.py', 'ark_amn.py', 'verify_amn.py')]),
 (r'C:\ALLOOLOO', 'https://github.com/allooloo/cm-kg.git', [(p, 'SITE/IW-MOVE/' + p.name) for p in sorted(H.glob('*.py'))]),
]
for root, want, files in SETS:
    rc, url, _ = git(root, 'remote', 'get-url', 'origin'); print('==', root, '· origin', url)
    if url != want: sys.exit(f'STOP: origin is not {want} — nothing pushed')
    hits = [(str(s), k) for s, _ in files for k, p in PAT.items() if re.search(p, pathlib.Path(s).read_text(encoding='utf-8', errors='replace'))]
    if hits: sys.exit(f'STOP: key-shape hit {hits}')
    changed = [d for s, d in files if (root == r'C:\ALLOOLOO') or place(s, os.path.join(root, d))]; print('  files', len(files), 'to commit', changed)
    if MODE != 'commit' or not changed: continue
    git(root, 'add', '--', *changed); rc, o, e = git(root, 'commit', '-m', MSG, '--', *changed); print('  commit', rc, (o or e)[-160:])
    rc, o, e = git(root, 'log', '-1', '--format=%h %s'); print('  ', o[:120]); rc, o, e = git(root, 'push', 'origin', 'HEAD'); print('  push exit', rc, e[-200:])
