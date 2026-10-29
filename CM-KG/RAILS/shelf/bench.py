r"""SHELF-01 step 4 (Bench) — the test set of one sealed market-year: issuers × dated questions × the answer with its source page.
Built once when the ledger marks the market complete and the year's manifest verifies; rebuilt only on a manifest change.
Sample: a fixed sample of issuers (N=500 where the year holds more, every issuer otherwise; seeded by the manifest's hash tree root, so the same manifest
always draws the same sample). Questions come only from what the sealed rows state — never from a later read:
  count        "How many <type> filings did <issuer> make in the quarter ending <D>?"            answer: an integer
  first_after  "What was the first filing <issuer> made after <D>?"                               answer: its date (and the filing it is)
  period_end   "What period end did the <form> that <issuer> filed on <D> report?"                where the row states one
  auditor      "Which firm was named as auditor in the annual report <issuer> filed on <D>?"      where the row names one
Publishes bench-<cc>-<year>.json (questions, signed; public) to the apex store shelf/bench/; the answers and source pages go to shelf-private/bench/ (never
served; the scoring door reads them). Questions are public; answers never leave the scoring door.
score(cc, year, answers) is the scoring door's rule: per question pass/fail, the score, the scorecard (signed).
Usage: python -X utf8 -I bench.py build <cc> <year> [--dry]
       python -X utf8 -I bench.py score <cc> <year> <answers.json>"""
import os, sys, json, re, random, datetime, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'isin-dis'), os.path.join(HERE, '..', 'backfill')]
N = 500
from score import pe_of
def apex_cont(name):
    """a container of the apex store (allooloocmkgapex), reached with the order ledger's own credential (managed identity on a job, account key on the laptop)"""
    import backfill as BF
    from azure.storage.blob import ContainerClient
    return ContainerClient(f'https://{BF.ORDER_SA}.blob.core.windows.net', name, credential=BF.ledger().credential)
def qend(d):
    y, m = int(d[:4]), int(d[5:7]); qm = ((m - 1) // 3 + 1) * 3
    return (datetime.date(y + (qm // 12), qm % 12 + 1, 1) - datetime.timedelta(days=1)).isoformat() if qm < 12 else f'{y}-12-31'
def questions(cc, year, rows, root):
    by = collections.defaultdict(list)
    for r in rows: by[(r.get('exchange'), r.get('ticker'), r.get('issuer'))].append(r)
    keys = sorted(by); rnd = random.Random(root)
    sample = keys if len(keys) <= N else rnd.sample(keys, N)
    Q, A = [], []
    for (ex, tk, nm) in sample:
        rs = sorted(by[(ex, tk, nm)], key=lambda r: (r['date'], r['url'])); who = f'{nm} ({ex}:{tk})'
        r0 = rnd.choice(rs); t0 = r0.get('event_type'); qe = qend(r0['date'])
        n = sum(1 for r in rs if r.get('event_type') == t0 and qend(r['date']) == qe)
        Q.append({'id': f'{cc}-{year}-{len(Q) + 1:04d}', 'kind': 'count', 'issuer': who, 'as_of': qe, 'question': f'How many {t0} filings did {who} make in the quarter ending {qe}?'})
        A.append({'id': Q[-1]['id'], 'answer': n, 'sources': [r['url'] for r in rs if r.get('event_type') == t0 and qend(r['date']) == qe]})
        d0 = (datetime.date.fromisoformat(rs[0]['date'][:10]) - datetime.timedelta(days=rnd.randint(1, 20))).isoformat()
        nxt = next((r for r in rs if r['date'][:10] > d0), None)
        if nxt:
            Q.append({'id': f'{cc}-{year}-{len(Q) + 1:04d}', 'kind': 'first_after', 'issuer': who, 'as_of': d0, 'question': f'What was the date of the first filing {who} made after {d0}?'})
            A.append({'id': Q[-1]['id'], 'answer': nxt['date'][:10], 'filing': nxt.get('title'), 'sources': [nxt['url']]})
        pe = next((r for r in rs if pe_of(r)), None)   # the period end the filing states (row field, or EDGAR's period of report on a periodic form)
        if pe:
            Q.append({'id': f'{cc}-{year}-{len(Q) + 1:04d}', 'kind': 'period_end', 'issuer': who, 'as_of': pe['date'][:10], 'question': f"What period end did the {pe.get('category') or 'filing'} that {who} filed on {pe['date'][:10]} report?"})
            A.append({'id': Q[-1]['id'], 'answer': pe_of(pe), 'sources': [pe['url']]})
        au = next((r for r in rs if r.get('auditor_named')), None)
        if au:
            Q.append({'id': f'{cc}-{year}-{len(Q) + 1:04d}', 'kind': 'auditor', 'issuer': who, 'as_of': au['date'][:10], 'question': f"Which firm was named as auditor in the annual report {who} filed on {au['date'][:10]}?"})
            A.append({'id': Q[-1]['id'], 'answer': au['auditor_named'], 'sources': [au.get('auditor_source') or au['url']]})
    return Q, A
norm = lambda s: re.sub(r'[^a-z0-9]+', ' ', str(s).lower().replace('&', ' and ')).replace(' llp', '').replace(' lp', '').strip()
def score(answers_key, given):
    """the scoring door's rule: exact integer for count; ISO date for first_after and period_end; firm name (case, punctuation and LLP set aside) for auditor"""
    want = {a['id']: a for a in answers_key}; per = []
    for g in given:
        a = want.get(g.get('id'))
        if not a: per.append({'id': g.get('id'), 'pass': False, 'why': 'unknown question'}); continue
        got = g.get('answer'); exp = a['answer']
        ok = (str(got).strip() == str(exp)) if isinstance(exp, int) else (str(got).strip()[:10] == exp if re.match(r'^\d{4}-\d{2}-\d{2}$', str(exp)) else norm(got) == norm(exp))
        per.append({'id': a['id'], 'pass': bool(ok)})
    n = len(want); p = sum(1 for x in per if x['pass'])
    return {'questions': n, 'answered': len(given), 'passed': p, 'score': round(100.0 * p / n, 1) if n else None, 'per_question': per}
def main():
    a = sys.argv[1:]; mode, cc, year = a[0], a[1], int(a[2]); dry = '--dry' in a
    import store, backfill as BF
    from replay_index import newest_manifest, year_rows
    c = store.cont(cc)
    if mode == 'build':
        led = BF.order_get(cc)
        if not (led and led.get('complete')): print(f'{cc}: ledger entry not complete — no bench'); return
        mn = newest_manifest(c, year); man = store.bj(c, mn); ok, rows = year_rows(c, man)   # streamed and checked (SHELF-01 2026-10-27, us scale)
        if not ok: print(f'{cc} {year}: manifest does not verify — no bench'); return
        Q, A = questions(cc, year, rows, man['hash_tree_root'])
        pub = BF.sign({'bench': f'bench-{cc}-{year}', 'market': cc, 'year': year, 'manifest': {'name': mn, 'hash_tree_root': man['hash_tree_root'], 'rows': man['rows'], 'signature': man['signature']},
                       'sample': {'rule': f'N={N} issuers where the year holds more, every issuer otherwise; seeded by the manifest root', 'issuers': len({q['issuer'] for q in Q})},
                       'kinds': dict(collections.Counter(q['kind'] for q in Q)), 'questions': Q, 'built_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       'scoring': 'answers are scored at the scoring door (score_bench); the answers and their source pages never leave it'})
        key = BF.sign({'bench': f'bench-{cc}-{year}', 'manifest_root': man['hash_tree_root'], 'answers': A})
        print(f"bench-{cc}-{year}: {len(Q)} questions on {pub['sample']['issuers']} issuers · kinds {pub['kinds']}")
        if not dry:
            for cont, name, doc in (('shelf', f'bench/bench-{cc}-{year}.json', pub), ('shelf-private', f'bench/answers-{cc}-{year}.json', key)):
                cc_ = apex_cont(cont)
                try: cc_.create_container()
                except Exception: pass
                cc_.upload_blob(name, json.dumps(doc, ensure_ascii=False).encode(), overwrite=True)
            print('published', f'shelf/bench/bench-{cc}-{year}.json', '· answers held at', f'shelf-private/bench/answers-{cc}-{year}.json')
        json.dump({'questions': Q[:10]}, open(os.path.join(os.environ.get('TEMP', '/tmp'), f'bench-{cc}-{year}-sample.json'), 'w'), indent=1)   # questions only: answers never leave the scoring door
    elif mode == 'score':
        given = json.load(open(a[3], encoding='utf-8')); key = json.load(open(a[4], encoding='utf-8')) if len(a) > 4 else None
        print(json.dumps(score(key['answers'], given)['score']))
if __name__ == '__main__': main()
