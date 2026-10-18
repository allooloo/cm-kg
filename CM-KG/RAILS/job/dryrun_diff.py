r"""ORDER-031 part 4 — the dry-run diff: one node's staging run against the 2026-10-16 record (START_ME_UP\allooloo-handoff-2026-10-17.json).
PASS = the job wrote its done-marker, records >= 10-16, events >= 10-16, the gate passed (not held), and the NUMBERS LOG line is well-formed.
  python dryrun_diff.py <cc> [market date] [container]      default container 'staging'"""
import os, sys, json, re, subprocess, datetime
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
NODES = {'nl': 'westeurope', 'ch': 'switzerlandnorth', 'fr': 'francecentral', 'de': 'germanywestcentral', 'sg': 'southeastasia', 'au': 'australiaeast', 'uk': 'uksouth', 'ca': 'canadacentral', 'jp': 'japaneast', 'kr': 'koreacentral', 'us': 'eastus'}
cc = sys.argv[1]; d = datetime.date.today(); mdate = sys.argv[2] if len(sys.argv) > 2 else (d - datetime.timedelta(days=(d.weekday() - 4) % 7)).isoformat(); cont = sys.argv[3] if len(sys.argv) > 3 else 'staging'
def az(*a, raw=False):
    p = subprocess.run(['az', *a] + ([] if raw else ['-o', 'json']), capture_output=True, text=True, encoding='utf-8', errors='replace', shell=(os.name == 'nt'))
    if p.returncode != 0: raise SystemExit(f"az {' '.join(a[:4])} failed: {(p.stderr or p.stdout)[-300:]}")
    return p.stdout.strip() if raw else (json.loads(p.stdout) if p.stdout.strip() else None)
acct = az('account', 'show')
if acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
from azure.storage.blob import BlobServiceClient
sa = f'allooloocmkg{cc}pond'; key = az('storage', 'account', 'keys', 'list', '-n', sa, '-g', f'allooloo-cmkg-{NODES[cc]}', '--query', '[0].value', '-o', 'tsv', raw=True)
c = BlobServiceClient(f'https://{sa}.blob.core.windows.net', credential=key).get_container_client(cont)
def get(n):
    try: return json.loads(c.get_blob_client(n).download_blob().readall().decode('utf-8'))
    except Exception: return None
base = json.load(open(r'C:\ALLOOLOO\START_ME_UP\allooloo-handoff-2026-10-17.json', encoding='utf-8'))['record']['nodes'][cc]
done = get(f'sweeps/{mdate}/{cc}/done.json'); failed = get(f'sweeps/{mdate}/{cc}/failed.json'); facts = get('door/facts.json'); n = ((facts or {}).get('nodes') or {}).get(f'{cc}-cm-kg') or {}
checks = []
checks.append(('done-marker written', bool(done), f"sweeps/{mdate}/{cc}/done.json" + ('' if done else f" missing{' — failed.json: ' + (failed or {}).get('error', '') if failed else ''}")))
if done:
    checks.append(('records >= 2026-10-16', done['records'] >= base['records'], f"{done['records']} vs {base['records']} ({done['records'] - base['records']:+d})"))
    checks.append(('events >= 2026-10-16', done['events'] >= base['events'], f"{done['events']} vs {base['events']} ({done['events'] - base['events']:+d})"))
    checks.append(('forward-only gate passed', done.get('gate_exit') == 0 and not done.get('held'), f"gate exit {done.get('gate_exit')}, held {done.get('held')}"))
    checks.append(('NUMBERS LOG line well-formed', bool(re.match(rf'^{cc}-cm-kg · \d{{4}}-\d{{2}}-\d{{2}} · \d+ · \d+ · records [+-]\d+ · events [+-]\d+', done.get('numbers_line', ''))), done.get('numbers_line', '')))
    checks.append(('as_of = market date', (done.get('as_of') == mdate) or (cc == 'us' and n.get('as_of') == mdate), f"{done.get('as_of')} (door facts {n.get('as_of')}) vs {mdate}"))
    checks.append(('door facts in the container match', n.get('records') == done['records'] and n.get('events') == done['events'], f"{cont}/door/facts.json records {n.get('records')} events {n.get('events')}"))
    checks.append(('pond drop named', bool(done.get('pond_drop')), str(done.get('pond_drop'))))
ok = all(p for _, p, _ in checks)
for name, p, detail in checks: print(f"{'PASS' if p else 'FAIL'}  {name}: {detail}")
print(f"\n{cc}-cm-kg dry run {mdate} on {sa}/{cont}: {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
