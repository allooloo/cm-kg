r"""patch_meter.py — FIX-01 item 2: the Tavily meter as a hard stop inside the one job, and the figure the digest prints.
  the stop     the $500 meter (62,500 credits) is SHARED OUT before anything starts: in yield order each market's run gets
               min(its approved run ceiling, what is left of the meter); a market reached after the meter is used up gets 0. Each market's guard counts
               every call against that number BEFORE the call leaves (tavily_guard.py: `elif RUN <= 0 or s["credits"] + n > RUN`), so the sum of what the
               34 runs can spend is <= the meter by arithmetic — it does not depend on Tavily's own account counter.
  the approved ceiling stays on each job as TAVILY_RUN_CEILING_APPROVED (set once from TAVILY_RUN_CEILING); the run's share is TAVILY_RUN_CEILING and
               is put back to the approved figure when the run ends.
  the figure   credits this run = the sum of the 34 guards' own ledgers (calls that left). The account counter's start and end are kept beside it; when
               the counter went DOWN (Tavily reset it mid-run, as on 2026-11-12) the digest says so instead of printing the difference.
Every replacement must match once. A .pre copy is kept. Usage: python -X utf8 -I patch_meter.py"""
import ast, pathlib, shutil, sys
p = pathlib.Path(r'C:\ALLOOLOO\CM-KG\RAILS\job\job_reslate.py'); pre = p.with_name('job_reslate.pre-fix01-2026-11-12.py'); s = p.read_text(encoding='utf-8')
if 'run_meter' in s: sys.exit('already patched')
if not pre.exists(): shutil.copy2(p, pre)
def rep(o, n):
    global s
    if s.count(o) != 1: sys.exit(f'STOP: {s.count(o)} of 1 for {o[:90]!r}')
    s = s.replace(o, n)
rep("rc = int(env.get('TAVILY_RUN_CEILING') or 0)", "rc = int(env.get('TAVILY_RUN_CEILING_APPROVED') or env.get('TAVILY_RUN_CEILING') or 0)")
rep("    plan.sort(key=lambda p: (-p['yield'], p['cc'])); S['yield_order'] = [p['cc'] for p in plan]; log('yield order:', ' '.join(S['yield_order']))\n",
    "    plan.sort(key=lambda p: (-p['yield'], p['cc'])); S['yield_order'] = [p['cc'] for p in plan]; log('yield order:', ' '.join(S['yield_order']))\n"
    "    # FIX-01 THE HARD STOP: the meter is shared out in yield order before anything starts; each guard refuses the call that would pass its share\n"
    "    meter_left = TAV_CREDITS\n"
    "    for p in plan: p['run_meter'] = max(0, min(p['run_ceiling'], meter_left)); meter_left -= p['run_meter']\n"
    "    assert sum(p['run_meter'] for p in plan) <= TAV_CREDITS, 'the shares pass the Tavily meter'\n"
    "    S['tavily']['shared_out'] = sum(p['run_meter'] for p in plan); S['tavily']['no_share'] = [p['cc'] for p in plan if p['run_ceiling'] and not p['run_meter']]; log('Tavily meter shared out:', S['tavily']['shared_out'], 'of', TAV_CREDITS, 'credits · no share:', ' '.join(S['tavily']['no_share']) or 'none')\n")
rep("f\"RESEARCH_PPLX_METER={p['pplx_meter']}\", 'RESEARCH_CHAIN=1']", "f\"RESEARCH_PPLX_METER={p['pplx_meter']}\", 'RESEARCH_CHAIN=1', f\"TAVILY_RUN_CEILING_APPROVED={p['run_ceiling']}\", f\"TAVILY_RUN_CEILING={p['run_meter']}\"]")
rep("log(p['cc'], 'started', p['execution'], 'run ceiling', p['run_ceiling'], 'yield', p['yield'])", "log(p['cc'], 'started', p['execution'], 'Tavily share', p['run_meter'], 'of approved', p['run_ceiling'], 'yield', p['yield'])")
rep("        az('containerapp', 'job', 'update', '-n', p['job'], '-g', p['rg'], '--remove-env-vars', 'NIGHT', 'FILL_CONFIRM', 'NIGHTLY_WINDOW_DAYS', 'RESEARCH_PPLX_METER', check=False)\n",
    "        az('containerapp', 'job', 'update', '-n', p['job'], '-g', p['rg'], '--remove-env-vars', 'NIGHT', 'FILL_CONFIRM', 'NIGHTLY_WINDOW_DAYS', 'RESEARCH_PPLX_METER', check=False)\n"
    "        az('containerapp', 'job', 'update', '-n', p['job'], '-g', p['rg'], '--set-env-vars', f\"TAVILY_RUN_CEILING={p['run_ceiling']}\", check=False)   # the approved ceiling goes back\n")
rep("S['tavily']['account_at_end'] = acc1; cr = (used1 - used0) if used0 is not None and used1 is not None else None",
    "S['tavily']['account_at_end'] = acc1; cr_acct = (used1 - used0) if used0 is not None and used1 is not None else None")
rep("    S['tavily'].update({'credits_this_run': cr,", "    cr = sum(int(((p.get('done') or {}).get('tavily_guard') or {}).get('credits') or 0) for p in plan)   # FIX-01: what the guards let out, not a difference of Tavily's counter\n"
    "    S['tavily'].update({'account_counter_delta': cr_acct, 'account_counter_reset': bool(cr_acct is not None and cr_acct < 0), 'credits_this_run': cr,")
rep("'20-tavily.txt': f\"Tavily this run: {cr if cr is not None else 'not read'} credits\" + (f\" = ${cr * USD_PER_CREDIT:.2f}\" if cr is not None else '') + f\" of the ${TAV_USD:.0f} meter",
    "'20-tavily.txt': f\"Tavily this run: {cr} credits = ${cr * USD_PER_CREDIT:.2f} (the guards' ledgers) of the ${TAV_USD:.0f} meter, {S['tavily']['shared_out']} credits shared out\" + (' · the account counter was reset by Tavily during the run' if S['tavily']['account_counter_reset'] else '') + f\"")
ast.parse(s); p.write_text(s, encoding='utf-8', newline='\n'); print('patched; .pre copy', pre.name)
