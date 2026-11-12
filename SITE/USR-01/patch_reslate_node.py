r"""patch_reslate_node.py — RESLATE-01: the market job (CM-KG\RAILS\job\job_node.py; job_node.py.pre-reslate01-2026-11-12 beside).
  · after the door is published (never on a held night, never in backfill mode) the Data Research chain runs for this market (RAILS\research\chain.py);
    a chain that fails is logged and named in the marker — it never fails the market's sweep
  · the marker (done.json) carries the Tavily guard's ledger for this run (credits, calls, denied = the unread tail at the meter, stopped) and the
    research summary, so the re-slate job reads the run's Tavily use and its tail from the markers
Idempotent. Usage: python -X utf8 -I patch_reslate_node.py"""
import pathlib, shutil
p = pathlib.Path(r'C:\ALLOOLOO\CM-KG\RAILS\job\job_node.py'); s = p.read_text(encoding='utf-8')
if 'RESLATE-01' in s: raise SystemExit('already patched')
shutil.copy2(p, p.with_name('job_node.py.pre-reslate01-2026-11-12'))
def rep(o, n):
    global s
    assert s.count(o) == 1, (s.count(o), o[:70]); s = s.replace(o, n)
rep("    # SPEND: the node's own lab lines from its drops (Canada carries the labs; the others call Tavily only) + its share of the Tavily counter\n",
    "    # RESLATE-01 (2026-11-12): the Data Research chain for this market, after its door is published — pull, roll-up, orderability, coverage, writer, exchange\n"
    "    # pages — from this market's own store, with its own keys; state in the store (research/). Never on a held night; a failed chain never fails the sweep.\n"
    "    research = {'ran': False}\n"
    "    if os.environ.get('RESEARCH_CHAIN', '1') == '1' and not hold and os.environ.get('JOB_MODE') != 'backfill' and CONT == 'pond':\n"
    "        try:\n"
    "            rc_rs = sh(['/usr/local/bin/python3', '-X', 'utf8', 'chain.py', CC, NIGHT], cwd=f'{RAILS}/research', check=False); log('research chain exit', rc_rs)\n"
    "            research = json.load(open(f'/tmp/research-{CC}.json', encoding='utf-8')) if os.path.exists(f'/tmp/research-{CC}.json') else {'ok': False, 'error': 'no summary written'}; research['ran'] = True; research['exit'] = rc_rs\n"
    "        except Exception as e: research = {'ran': True, 'ok': False, 'error': repr(e)[:300]}; log('research chain FAILED:', research['error'])\n"
    "    elif hold: research['why'] = 'the door is held: the pages stay as they were'\n"
    "    # RESLATE-01: the Tavily guard's ledger of this run (credits, calls, denied = the reads left unread at the meter, stopped) into the marker\n"
    "    guard = None\n"
    "    try:\n"
    "        import tempfile as _tf; _gl = os.environ.get('TAVILY_LEDGER') or os.path.join(_tf.gettempdir(), f\"tavily-guard-{os.environ.get('CONTAINER_APP_JOB_EXECUTION_NAME', 'local')}.json\")\n"
    "        guard = json.load(open(_gl, encoding='utf-8')) if os.path.exists(_gl) else {'credits': 0, 'calls': 0, 'denied': 0, 'stopped': None, 'note': 'no Tavily call was attempted'}\n"
    "        guard['run_ceiling'] = os.environ.get('TAVILY_RUN_CEILING'); guard['approved'] = os.environ.get('TAVILY_APPROVED')\n"
    "    except Exception as e: guard = {'error': repr(e)[:200]}\n"
    "    # SPEND: the node's own lab lines from its drops (Canada carries the labs; the others call Tavily only) + its share of the Tavily counter\n")
rep("'tavily': {'start': tav0, 'end': tav1}, 'ark': ark,", "'tavily': {'start': tav0, 'end': tav1}, 'tavily_guard': guard, 'research': research, 'ark': ark,")
p.write_text(s, encoding='utf-8'); print('patched')
