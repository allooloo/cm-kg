r"""grok_table.py — FIX-01 item 3: every Grok call of the 2026-11-12 run, by rail, from each market's own record (done.json) and its coverage state.
  sweep rails      the market sweep's own spend line "Grok (grok-4.6) · N calls · … · $X" (Fill + Confirm / width rails inside cmkg-<cc>-rail)
  research rail    the coverage step's closing ledger (grok_calls, grok_usd) — the second read, in the image that ran before the strike — and what it
                   returned: rows in research/state/coverage.jsonl whose engine line names Grok as the reader that found the page or note
Read only. Writes grok-table.json. Usage: python -X utf8 grok_table.py"""
import json, re, sys, os
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\isin-dis'); import store
H = os.path.dirname(os.path.abspath(__file__)); M = json.load(open(os.path.join(H, 'markers-2026-11-12.json'))); out = {}; T = {'sweep_calls': 0, 'sweep_usd': 0.0, 'cov_calls': 0, 'cov_usd': 0.0, 'cov_returned': 0}
for cc, m in M.items():
    d = m.get('done') or {}; row = {'sweep_calls': 0, 'sweep_usd': 0.0, 'cov_calls': 0, 'cov_usd': 0.0, 'cov_returned': None, 'cov_returned_page': None}
    for l in d.get('spend_lines') or []:
        g = re.search(r'Grok \(([^)]*)\) · ([\d,]+) calls · ([\d,]+) in / ([\d,]+) out · \$([\d.,]+)', str(l))
        if g: row['sweep_calls'] = int(g.group(2).replace(',', '')); row['sweep_usd'] = float(g.group(5).replace(',', '')); row['sweep_in'] = int(g.group(3).replace(',', ''))
    last = str((((d.get('research') or {}).get('steps') or {}).get('coverage') or {}).get('last') or ''); j = re.search(r'\{.*\}', last)
    gc = re.search(r'"grok_calls": (\d+)', last); gu = re.search(r'"grok_usd": ([\d.]+)', last); gi = re.search(r'"grok_in": (\d+)', last)
    if gc: row['cov_calls'] = int(gc.group(1)); row['cov_usd'] = round(float(gu.group(1)), 2) if gu else None; row['cov_in'] = int(gi.group(1)) if gi else None
    if row['cov_calls']:
        try:
            ret = page = 0
            for l in store.cont(cc).download_blob('research/state/coverage.jsonl').readall().decode('utf-8').splitlines():
                if 'Grok' in l:
                    r = json.loads(l)
                    if 'Grok' in str(r.get('engine') or ''): ret += 1; page += bool((r.get('answer') or r).get('coverage_page'))
            row['cov_returned'] = ret; row['cov_returned_page'] = page
        except Exception as e: row['cov_err'] = repr(e)[:120]
    out[cc] = row
    for k in ('sweep_calls', 'sweep_usd', 'cov_calls', 'cov_usd'): T[k] += row[k] or 0
    T['cov_in'] = T.get('cov_in', 0) + (row.get('cov_in') or 0)
    T['cov_returned'] += row['cov_returned'] or 0
    if row['sweep_calls'] or row['cov_calls']: print(cc, row, flush=True)
T = {k: round(v, 2) for k, v in T.items()}; print('TOTAL', T); json.dump({'markets': out, 'total': T}, open(os.path.join(H, 'grok-table.json'), 'w'), indent=1)
