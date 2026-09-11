r"""Door store on D1 (CEO order 2026-09-11: token AGENT KEYS\cloudflare-d1.txt). Reads the node outputs already rendered by load_nodes.py under
CM-KG\DOOR\data\ (records/<node>/<EX>/<TICKER>.json, events/…, index.json, facts.json, nodes.json) and loads them into ONE D1 database (cm-kg,
node column) through `wrangler d1 execute --remote --file`. Tables (schema.sql): records (cmr PK, node, exchange, ticker, name, isin, lei, as_of,
version, json), events (cmr, date, json; index on cmr, date), idx (kind, value, cmr; kinds cmr, ticker, isin, lei, alias, name), meta (k, json:
facts, nodes). Idempotent: every node load is DELETE-then-INSERT for that node, in SQL files of at most 4,000 statements.
Usage: python load_d1.py [node ...]   (default: every node present under data/records). Never prints the token."""
import os, sys, json, glob, subprocess, time
DOOR = r'C:\ALLOOLOO\CM-KG\DOOR'; DATA = os.path.join(DOOR, 'data'); OUT = os.path.join(DOOR, 'd1'); DB = 'cm-kg'
os.makedirs(OUT, exist_ok=True)
def q(s):
    if s is None: return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"
def nkey(s):
    import re; return re.sub(r'[^a-z0-9]+', ' ', str(s).lower().replace('&', ' and ')).strip()
def run_sql_file(path):
    env = dict(os.environ); env['CLOUDFLARE_API_TOKEN'] = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare-d1.txt', encoding='utf-8').read().strip(); env['CLOUDFLARE_ACCOUNT_ID'] = 'dd2832b36f171b815f84c8487aada36b'
    for attempt in range(3):
        p = subprocess.run(['npx', '--yes', 'wrangler', 'd1', 'execute', DB, '--remote', '--yes', '--file=' + path], cwd=DOOR, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', shell=True)
        if p.returncode == 0: return True
        print('  retry', os.path.basename(path), (p.stderr or p.stdout)[-300:].replace('\n', ' '), flush=True); time.sleep(10)
    raise SystemExit('D1 execute failed for ' + path)
def write_batches(name, stmts, per=4000):
    files = []
    for i in range(0, len(stmts), per):
        fn = os.path.join(OUT, f'{name}-{i // per:03d}.sql'); open(fn, 'w', encoding='utf-8').write('\n'.join(stmts[i:i + per]) + '\n'); files.append(fn)
    return files
def load_node(node):
    recs = glob.glob(os.path.join(DATA, 'records', node, '*', '*.json')); print(node, 'records', len(recs), flush=True)
    stmts = [f"DELETE FROM events WHERE cmr IN (SELECT cmr FROM records WHERE node = {q(node)});", f"DELETE FROM idx WHERE cmr IN (SELECT cmr FROM records WHERE node = {q(node)});", f"DELETE FROM records WHERE node = {q(node)};"]
    n_ev = 0
    for fn in recs:
        r = json.load(open(fn, encoding='utf-8')); cmr = r['cmr']; _, ex, t = cmr.split('/', 2); idn = r['identity']
        v = lambda f: (idn.get(f) or {}).get('value')
        stmts.append(f"INSERT INTO records (cmr, node, exchange, ticker, name, isin, lei, as_of, version, json) VALUES ({q(cmr)}, {q(node)}, {q(ex)}, {q(t)}, {q(v('name'))}, {q(v('isin'))}, {q(v('lei'))}, {q(r['as_of'])}, {int(r['version'])}, {q(json.dumps(r, ensure_ascii=False, separators=(',', ':')))});")
        keys = {('cmr', cmr.upper()), ('ticker', t.upper())}
        root = t.split('.')[0].upper()
        if root != t.upper(): keys.add(('ticker', root))
        if v('isin'): keys.add(('isin', str(v('isin')).upper()))
        if v('lei'): keys.add(('lei', str(v('lei')).upper()))
        if v('name'): keys.add(('name', nkey(v('name'))))
        for a in r.get('aliases', []):
            if a.get('value'): keys.add(('alias', nkey(a['value'])))
        for kind, val in keys: stmts.append(f"INSERT INTO idx (kind, value, cmr) VALUES ({q(kind)}, {q(val)}, {q(cmr)});")
        ef = fn.replace(os.path.join(DATA, 'records'), os.path.join(DATA, 'events'))
        if os.path.exists(ef):
            for e in json.load(open(ef, encoding='utf-8')):
                stmts.append(f"INSERT INTO events (cmr, date, json) VALUES ({q(cmr)}, {q(e.get('date'))}, {q(json.dumps(e, ensure_ascii=False, separators=(',', ':')))});"); n_ev += 1
    files = write_batches(node, stmts); print(node, 'statements', len(stmts), 'events', n_ev, 'files', len(files), flush=True)
    for i, f in enumerate(files):
        run_sql_file(f)
        if i % 5 == 0: print('  ', node, i + 1, '/', len(files), flush=True)
    return len(recs), n_ev
def load_meta():
    facts = json.load(open(os.path.join(DATA, 'facts.json'), encoding='utf-8')); nodes = json.load(open(os.path.join(DATA, 'nodes.json'), encoding='utf-8'))
    facts['store'] = 'Cloudflare D1 (one database, node column)'
    stmts = [f"INSERT OR REPLACE INTO meta (k, json) VALUES ('facts', {q(json.dumps(facts, ensure_ascii=False))});", f"INSERT OR REPLACE INTO meta (k, json) VALUES ('nodes', {q(json.dumps(nodes, ensure_ascii=False))});"]
    fn = os.path.join(OUT, 'meta.sql'); open(fn, 'w', encoding='utf-8').write('\n'.join(stmts) + '\n'); run_sql_file(fn); print('meta loaded', flush=True)
if __name__ == '__main__':
    run_sql_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')); print('schema ok', flush=True)
    want = sys.argv[1:] or sorted(os.listdir(os.path.join(DATA, 'records')))
    totals = {}
    for node in want: totals[node] = load_node(node)
    load_meta()
    print('DONE', totals, flush=True)
