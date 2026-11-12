r"""chain.py — RESLATE-01 (2026-11-12): the Data Research chain for one market, run inside that market's own job after its door is published
(job_node.py), from the market's own store and with the market's own keys:  pull → roll-up → orderability → coverage → writer → exchange pages.
State lives in the market's store (container pond, prefix research/), so the job image holds none:
  research/state/pages.jsonl      the pages as last written (the writer's write-on-change ledger)
  research/state/coverage.jsonl   the coverage and open-research read as it stands per issuer (the newest read of each)
  research/out/<night>/           this run's manifest, numbers, exchange pages, the coverage tail and the summary
YIELD FIRST: the coverage read goes in order of yield (most filings first) up to its meter (RESEARCH_PPLX_METER, $); the unread set is the tail — its
issuers keep their last read — and is named in the summary for the digest; the next run picks it up first... in the same order of yield.
Publishing to the page store is the re-slate job's step (publish_stores.py), not this one. A failed step stops the chain; the door is never touched.
Usage: python -X utf8 chain.py <cc> [night]"""
import sys, os, json, glob, subprocess, datetime, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'isin-dis')); import store
cc = sys.argv[1]; NIGHT = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('NIGHT') or datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
R = r'C:\ALLOOLOO\CM-KG\RESEARCH'; POND = r'C:\ALLOOLOO\CM-KG\POND'; TODAY = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
METER = os.environ.get('RESEARCH_PPLX_METER'); THREADS = os.environ.get('RESEARCH_THREADS', '24'); PY = sys.executable; S = {'node': f'{cc}-cm-kg', 'night': NIGHT, 'steps': {}}
c = store.cont(cc)
def get(name, path):
    try: data = c.download_blob(name).readall()
    except Exception as e:
        if 'BlobNotFound' in repr(e) or 'does not exist' in repr(e): return False
        raise
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, 'wb').write(data); return True
def put(name, path): c.upload_blob(name, open(path, 'rb').read(), overwrite=True)
def run(step, args):
    r = subprocess.run(args, cwd=HERE, capture_output=True, text=True, encoding='utf-8', errors='replace'); tail = (r.stdout or '').strip().splitlines()[-1:] or ['']
    S['steps'][step] = {'exit': r.returncode, 'last': tail[0][:300]}; print(step, 'exit', r.returncode, tail[0][:200], flush=True)
    if r.returncode: S['failed'] = step; S['error'] = ((r.stderr or '') + (r.stdout or ''))[-400:]; raise SystemExit(f'{step} failed')
try:
    pf = os.path.join(R, 'pages', f'{cc}.jsonl'); had = get('research/state/pages.jsonl', pf); S['pages_state_restored'] = had
    prior = {}
    cov0 = os.path.join(POND, f'{cc}-cm-kg', 'research-coverage', 'state.jsonl')
    if get('research/state/coverage.jsonl', cov0):
        for l in open(cov0, encoding='utf-8'): j = json.loads(l); prior[j['cmr']] = j
    before = {}
    if had:
        for l in open(pf, encoding='utf-8'): j = json.loads(l); before[j['cmr']] = j['numbers_hash']
    run('pull', [PY, '-X', 'utf8', 'pull.py', cc]); run('rollup', [PY, '-X', 'utf8', 'rollup.py', cc]); run('orderability', ['node', 'orderability.mjs', cc])
    cd = os.path.join(POND, f'{cc}-cm-kg', 'research-coverage', f'{TODAY}-9'); shutil.rmtree(cd, ignore_errors=True)
    run('coverage', [PY, '-X', 'utf8', 'coverage.py', cc, '--drop', f'{TODAY}-9', '--threads', THREADS] + (['--meter', METER] if METER else []))
    raw = os.path.join(cd, 'raw.jsonl'); read = {json.loads(l)['cmr'] for l in open(raw, encoding='utf-8')} if os.path.exists(raw) else set(); tail = json.load(open(os.path.join(cd, 'tail.json'))) if os.path.exists(os.path.join(cd, 'tail.json')) else {'tail': []}
    carried = 0
    with open(raw, 'a', encoding='utf-8') as f:   # an issuer not read this run keeps its last read (the tail, and any call that failed)
        for k, j in prior.items():
            if k not in read: f.write(json.dumps(j, ensure_ascii=False) + '\n'); carried += 1
    sp = json.load(open(os.path.join(cd, 'spend.json'))) if os.path.exists(os.path.join(cd, 'spend.json')) else {}
    S['coverage'] = {'read': len(read), 'tail_unread': len(tail.get('tail', [])), 'carried_from_last_read': carried, 'meter_usd': float(METER) if METER else None, 'perplexity_calls': sp.get('calls', 0), 'perplexity_usd': round(sp.get('cost', 0), 2), 'mistral_calls': sp.get('mistral_calls', 0), 'haiku_calls': sp.get('haiku_calls', 0), 'haiku_in': sp.get('haiku_in', 0), 'haiku_out': sp.get('haiku_out', 0)}
    # the writer joins the newest coverage drop by date and suffix: this run's drop (<today>-9)
    run('write', [PY, '-X', 'utf8', 'write.py', cc, '--threads', THREADS]); run('exchange', [PY, '-X', 'utf8', 'exchange.py', cc])
    man = json.load(open(os.path.join(R, 'pages', f'{cc}.manifest.json'))); wsp = json.load(open(os.path.join(R, 'pages', f'{cc}.spend.json'))) if os.path.exists(os.path.join(R, 'pages', f'{cc}.spend.json')) else {}
    after = {}
    for l in open(pf, encoding='utf-8'): j = json.loads(l); after[j['cmr']] = j['numbers_hash']
    S['pages'] = {'pages': man['pages'], 'prior_pages': len(before), 'new': len(set(after) - set(before)), 'changed': sum(1 for k in after if k in before and before[k] != after[k]), 'unchanged': sum(1 for k in after if before.get(k) == after[k]), 'left_the_record': len(set(before) - set(after)),
                  'written_this_run': man['written_this_run'], 'by_template': man['by_template'], 'coverage_found': man['coverage_found'], 'coverage_none_found': man['coverage_none_found'], 'coverage_not_read': man['coverage_not_read'], 'open_research_rows': man['open_research_rows'], 'record_as_of': man['record_as_of'], 'sha256': man['sha256'],
                  'writer_calls': wsp.get('calls', 0), 'writer_in': wsp.get('input_tokens', 0), 'writer_out': wsp.get('output_tokens', 0)}
    put('research/state/pages.jsonl', pf); put('research/state/coverage.jsonl', raw); o = f'research/out/{NIGHT}/'
    put(o + 'manifest.json', os.path.join(R, 'pages', f'{cc}.manifest.json')); put(o + 'numbers.jsonl', os.path.join(R, 'numbers', f'{cc}.jsonl')); put(o + 'exchanges.json', os.path.join(R, 'exchanges', f'{cc}.json'))
    c.upload_blob(o + 'coverage-tail.json', json.dumps(tail).encode(), overwrite=True); S['ok'] = True
except SystemExit: S['ok'] = False
except Exception as e: S['ok'] = False; S['error'] = repr(e)[:400]
try: c.upload_blob(f'research/out/{NIGHT}/summary.json', json.dumps(S, indent=1).encode(), overwrite=True)
except Exception as e: print('summary not uploaded', repr(e)[:200])
json.dump(S, open(os.path.join(os.environ.get('TMP', '/tmp') if os.name == 'nt' else '/tmp', f'research-{cc}.json'), 'w'), indent=1)
print('RESEARCH', cc, 'ok' if S.get('ok') else 'FAILED', json.dumps(S.get('pages') or S.get('error') or S.get('failed'))[:300], flush=True); sys.exit(0 if S.get('ok') else 1)
