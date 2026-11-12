r"""iw_tie.py — IW-MOVE-01 step 6: the two coverage-sample rows that differ between the sides. The sample is `ORDER BY landed_at DESC LIMIT 150`; this reads
landed_at of the four news ids (two only on each side) and of the 150th row of the shared sample, on BOTH databases, to show whether the four are tied at
the cut (the same record, a tie broken by the order rows sit on disk) or are different data. Read only. Usage: python -X utf8 -I iw_tie.py"""
import json, os, subprocess, pathlib
AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']; H = pathlib.Path(__file__).parent; PSQL = os.path.join('C:' + chr(92) + 'Program Files', 'PostgreSQL', '16', 'bin', 'psql.exe')
def rows(s): return [json.loads(l) for l in open(H / 'trial' / s / 'db' / 'coverage_check.jsonl', encoding='utf-8') if l.strip()]
o = {r['news_id'] for r in rows('old')}; n = {r['news_id'] for r in rows('new')}; ids = sorted((o - n) | (n - o)); out = {'only_old': sorted(o - n), 'only_new': sorted(n - o)}
for nm, cfg, sub, kv, sec, host in (('old', r'C:\A2AAMN\.azure', ['--subscription', '9e406344-81a4-4624-98de-a9c642a75d69'], 'kv-amn-frc', 'pg-amn-frc-admin', 'pg-amn-frc.postgres.database.azure.com'), ('new', r'C:\ALLOOLOO\.azure', [], 'allooloo-iw-kv-frc', 'pg-admin', 'allooloo-iw-pg-frc.postgres.database.azure.com')):
    pw = subprocess.run([*AZ, 'keyvault', 'secret', 'show', '--vault-name', kv, '-n', sec, *sub, '--query', 'value', '-o', 'tsv'], capture_output=True, text=True, env=dict(os.environ, AZURE_CONFIG_DIR=cfg)).stdout.strip()
    PE = dict(os.environ, PGPASSWORD=pw, PGSSLMODE='require'); del pw
    q = "select id, landed_at from amn.news where id in (" + ','.join("'" + i + "'" for i in ids) + ") order by 1"
    q2 = "select landed_at, count(*) from amn.news where landed_at = (select min(landed_at) from amn.news where id in (" + ','.join("'" + i + "'" for i in ids) + ")) group by 1"
    a = subprocess.run([PSQL, '-h', host, '-U', 'amnadmin', '-d', 'amn', '-At', '-c', q], capture_output=True, env=PE).stdout.decode().split(); b = subprocess.run([PSQL, '-h', host, '-U', 'amnadmin', '-d', 'amn', '-At', '-c', q2], capture_output=True, env=PE).stdout.decode().strip(); del PE
    out[nm] = {'landed_at_of_the_four': a, 'rows_sharing_that_landed_at': b}
json.dump(out, open(H / 'trial' / 'tie-check.json', 'w'), indent=1); print(json.dumps(out, indent=1))
