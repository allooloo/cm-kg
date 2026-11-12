r"""patch_reslate_iw.py — IW-MOVE-01 step 8: Issuerwire's schedule is the one weekly job, on the Allooloo side only. Adds to job_reslate.py a step that
runs Issuerwire's eight Ops Agents jobs (iw-<x>-rail in allooloo-iw-francecentral) once, in the cycle's own order, each awaited before the next; it runs
beside the markets (a thread) and is read before the digest, which gets its own line. Skippable: RESLATE_SKIP=issuerwire. Every replacement must match
once or the run stops. A .pre copy is kept. Usage: python -X utf8 -I patch_reslate_iw.py"""
import ast, pathlib, shutil, sys
p = pathlib.Path(r'C:\ALLOOLOO\CM-KG\RAILS\job\job_reslate.py'); pre = p.with_name('job_reslate.pre-iwmove01-2026-11-12.py'); s = p.read_text(encoding='utf-8')
if 'IW_ORDER' in s: sys.exit('already patched')
if not pre.exists(): shutil.copy2(p, pre)
def rep(o, n):
    global s
    if s.count(o) != 1: sys.exit(f'STOP: {s.count(o)} of 1 for {o[:80]!r}')
    s = s.replace(o, n)
rep("def main():\n", '''IW_RG = 'allooloo-iw-francecentral'; IW_ORDER = ['standing', 'filings', 'coverage', 'claims', 'receipts', 'ark', 'stores', 'close']
def issuerwire(out):
    """IW-MOVE-01: Issuerwire's cycle — its eight Ops Agents jobs, once, in order, each awaited (its own replica timeout bounds it). A job that fails does
    not stop the ones after it: each is its own duty and the digest names what failed."""
    for x in IW_ORDER:
        job = f'iw-{x}-rail'; t0 = time.time()
        try:
            j = az('containerapp', 'job', 'show', '-n', job, '-g', IW_RG); lim = int(j['properties']['configuration'].get('replicaTimeout') or 3600) + 600
            r = az('containerapp', 'job', 'start', '-n', job, '-g', IW_RG); ex = r.get('name') or r.get('id', '').split('/')[-1]; st = None
            while time.time() - t0 < lim:
                time.sleep(30); e = az('containerapp', 'job', 'execution', 'show', '-n', job, '-g', IW_RG, '--job-execution-name', ex, check=False); st = ((e or {}).get('properties') or {}).get('status')
                if st and st not in ('Running', 'Processing', 'Unknown'): break
            out[x] = {'execution': ex, 'status': st or 'no status', 'seconds': int(time.time() - t0)}
        except Exception as e: out[x] = {'status': 'NOT STARTED', 'error': repr(e)[:200]}
        log('issuerwire', x, out[x].get('status'), out[x].get('seconds'))
def main():
''')
rep("    deadline = time.time() + WAIT_H * 3600; left = [p for p in plan if p.get('execution')]\n",
    "    S['issuerwire'] = {}; iw_t = None\n"
    "    if 'issuerwire' not in SKIP and not ONLY:\n"
    "        import threading; iw_t = threading.Thread(target=issuerwire, args=(S['issuerwire'],), daemon=True); iw_t.start()\n"
    "    deadline = time.time() + WAIT_H * 3600; left = [p for p in plan if p.get('execution')]\n")
rep("    S['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()\n",
    "    if iw_t: iw_t.join(timeout=6 * 3600)\n"
    "    iw_bad = [x for x in IW_ORDER if (S['issuerwire'].get(x) or {}).get('status') != 'Succeeded'] if iw_t else []\n"
    "    S['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()\n")
rep("    for k, v in L.items(): put(ops,", "    if iw_t: L['40-issuerwire.txt'] = f\"Issuerwire {NIGHT}: {len(IW_ORDER) - len(iw_bad)} of {len(IW_ORDER)} Ops Agents jobs ran\" + (f\" · FAILED {' '.join(iw_bad)}\" if iw_bad else '') + ' · weekly, in the one job (iw-*-rail, allooloo-iw-francecentral)'\n    for k, v in L.items(): put(ops,")
rep("    return 1 if failed or (apex_rc not in (0, None)) else 0", "    return 1 if failed or iw_bad or (apex_rc not in (0, None)) else 0")
rep("RESLATE_SKIP (apex,others,publish,digest).", "RESLATE_SKIP (apex,others,publish,digest,issuerwire). Issuerwire (IW-MOVE-01): its eight Ops Agents jobs run once in this job, in order, beside the markets.")
ast.parse(s); p.write_text(s, encoding='utf-8', newline='\n'); print('patched job_reslate.py; .pre copy', pre.name)
