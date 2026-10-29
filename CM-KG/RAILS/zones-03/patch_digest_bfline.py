r"""ZONES-03 standing line (CEO 2026-10-27): the nightly digest carries a backfill line — market closed, years, manifests, ark objects, next waiting; any FAIL
named. Patches RAILS\job\job_digest.py (.pre kept). Read from the order ledger (backfill-order/<cc>.json, apex store), each market's backfill/facts.json, its
backfill/<year>/manifest.json files and its newest backfill done marker (ark line). Nothing typed; nothing else in the digest changes."""
import shutil, os
p = r'C:\ALLOOLOO\CM-KG\RAILS\job\job_digest.py'
pre = p + '.pre-bfline-20261027'
if not os.path.exists(pre): shutil.copy2(p, pre)
s = open(p, encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:90]
    s = s.replace(a, b)
# 1 · per market, inside the node loop: manifests in the store and the ark objects of its newest backfill run
rep("""            BF.append({'node': f'{cc}-cm-kg', 'year_in_progress': (bf or {}).get('year_in_progress'),""",
"""            # ZONES-03 standing line (2026-10-27): manifests held and the ark objects of the market's newest backfill run (its own done marker)
            mans = sum(1 for b in c.list_blobs(name_starts_with='backfill/') if re.match(r'backfill/\\d{4}/manifest\\.json$', b.name))
            lastm = sorted(b.name for b in c.list_blobs(name_starts_with='sweeps-backfill/') if b.name.endswith(f'/{cc}/done.json'))
            lm = get_json(c, lastm[-1]) if lastm else None; ak = re.search(r'ark: (\\d+) objects', clean((lm or {}).get('tail') or ''))
            BF.append({'manifests': mans, 'ark_objects_last_run': int(ak.group(1)) if ak else None, 'last_run_night': (lm or {}).get('night'),
                       'node': f'{cc}-cm-kg', 'year_in_progress': (bf or {}).get('year_in_progress'),""")
# 2 · the line, from the order ledger, before digest.json is written
rep("""    n_pass = sum(1 for r in rows if r['verdict'] == 'PASS'); n_fail = sum(1 for r in rows if r['verdict'] in ('FAIL', 'HELD'))""",
"""    # ZONES-03 standing line (2026-10-27): backfill — markets closed (ledger complete) with years, manifests and ark objects; the next market waiting; FAILs named
    bf_line = 'Backfill · not read (flag)'
    try:
        POLF = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backfill', 'policy.json'), encoding='utf-8'))
        codes = [cc for cc, _ in NODES]; order = [cc for cc in POLF['order'] if cc in codes and (POLF.get('markets') or POLF).get(cc, {}).get('adapter') != 'none']
        led = client(APEX_SA, akey, 'backfill-order'); bfx = {x['node'][:2]: x for x in BF}; closed = []; nxt = None
        for cc in order:
            e = get_json(led, f'{cc}.json') or {}
            if e.get('complete'):
                x = bfx.get(cc) or {}; ys = sorted(int(y) for y in (x.get('years_done') or []))
                closed.append(f"{cc} — years {ys[0]}–{ys[-1] if ys else ''} ({len(ys)}) · {x.get('manifests', '—')} manifests · ark {x.get('ark_objects_last_run', '—')} objects (run {x.get('last_run_night') or '—'})" if ys else f"{cc} — years not read")
            elif nxt is None: nxt = f"{cc} ({e.get('left', 'no ledger entry')} to do)" if e else f'{cc} (no ledger entry yet)'
        fails = [f"{x['node']}: {x['night'][len('FAILED: '):][:120]}" for x in BF if str(x.get('night') or '').startswith('FAILED')]
        bf_line = f"Backfill · closed: {' ; '.join(closed) or 'none'} · next waiting: {nxt or 'none (every market complete)'} · FAIL: {' ; '.join(fails) if fails else 'none'}"
    except Exception as e: bf_line = f'Backfill · not read (flag): {repr(e)[:120]}'
    n_pass = sum(1 for r in rows if r['verdict'] == 'PASS'); n_fail = sum(1 for r in rows if r['verdict'] in ('FAIL', 'HELD'))""")
rep("""'tavily_meter': tav, 'capacity': cap, 'backfill': BF,""", """'tavily_meter': tav, 'capacity': cap, 'backfill': BF, 'backfill_line': bf_line,""")
rep("""'## Backfill (Allooloo Datasets · BACKFILL-01)', '',""", """'## Backfill (Allooloo Datasets · BACKFILL-01)', '', bf_line, '',""")
rep("""<p>{cap_line0}</p><p>{cap_line}</p><table""", """<p>{cap_line0}</p><p>{cap_line}</p><p>{bf_line}</p><table""")
open(p, 'w', encoding='utf-8').write(s)
print('patched')
