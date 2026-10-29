r"""RADAR-02 (2026-10-23) — CM-KG/ESTATE/public/spend.json from SPEND.md, per lab per run; plain $ only, no currency codes. Run by the apex job every night after the
SPEND lines land and before the estate deploy, and by hand.
  python spend_json.py [tavily-usage.json]
  runs     the last eight runs in SPEND.md, one line per lab (run · lab · calls · tokens · $ · meter), $ as written ("USD 4.50" prints "$4.50")
  tavily   the meter (GET https://api.tavily.com/usage): plan used of plan limit, pay-as-you-go used of its ceiling — from the file the apex job wrote, else read here
           with the key named in AGENT KEYS (tavily.txt; the job carries it as TAVILY_API_KEY). Never typed.
  azure    month to date from the Cost Management API when it answers; else "not read" with the date tried."""
import os, sys, json, re, subprocess, datetime, urllib.request
ROOT = os.environ.get('CMKG_ROOT', r'C:\ALLOOLOO' if os.name == 'nt' else '/job/ALLOOLOO'); MD = os.path.join(ROOT, 'CM-KG', 'SPEND', 'SPEND.md'); OUT = os.path.join(ROOT, 'CM-KG', 'ESTATE', 'public', 'spend.json')
SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'; NOW = datetime.datetime.now(datetime.timezone.utc); STAMP = NOW.strftime('%Y-%m-%dT%H:%M:%SZ')
def plain(s): return re.sub(r'\bUSD\s*\$?\s*([\d.,]+)', r'$\1', re.sub(r'([\d.,]+)\s*USD\b', r'$\1', s)).replace('USDC', '').replace('  ', ' ').strip()
def parse(line):
    f = [x.strip() for x in line.split(' · ')]
    if len(f) < 3: return None
    money = next((x for x in f[2:] if re.search(r'\$\s*[\d.,]+|USD\s*[\d.,]+|[\d.,]+\s*USD', x)), None)
    calls = next((x for x in f[2:] if re.search(r'\bcalls?\b|\bpages\b|credits used|PUT requests', x)), None)
    tokens = next((x for x in f[2:] if re.search(r'\bin / [\d,]+ out\b', x)), None)
    meter = next((x for x in f[2:] if x.startswith(('meter', 'no meter'))), None)
    return {'run': f[0], 'lab': f[1], 'calls': plain(calls) if calls else None, 'tokens': tokens, 'figure': plain(money) if money else None, 'meter': plain(meter) if meter else None, 'line': plain(line)}
def tavily(path):
    j = None
    if path and os.path.exists(path):
        try: j = json.load(open(path, encoding='utf-8'))
        except Exception: j = None
    if j is None:
        k = os.environ.get('TAVILY_API_KEY') or (open(os.path.join(ROOT, 'AGENT KEYS', 'tavily.txt'), encoding='utf-8').read().strip().split()[-1] if os.path.exists(os.path.join(ROOT, 'AGENT KEYS', 'tavily.txt')) else '')
        try: j = json.load(urllib.request.urlopen(urllib.request.Request('https://api.tavily.com/usage', headers={'Authorization': 'Bearer ' + k}), timeout=30))
        except Exception as e: return {'state': f'not read ({type(e).__name__})', 'tried': STAMP}
    a = (j or {}).get('account') or {}
    if a.get('plan_usage') is None: return {'state': 'not read (no account block)', 'tried': STAMP}
    return {'state': 'read', 'read_at': STAMP, 'plan': a.get('current_plan'), 'plan_used': a.get('plan_usage'), 'plan_limit': a.get('plan_limit'), 'paygo_used': a.get('paygo_usage'), 'paygo_ceiling': a.get('paygo_limit'),
            'meter': 'GET https://api.tavily.com/usage (account block)'}
def azure():
    body = json.dumps({'type': 'ActualCost', 'timeframe': 'MonthToDate', 'dataset': {'granularity': 'None', 'aggregation': {'total': {'name': 'Cost', 'function': 'Sum'}}}})
    try:
        p = subprocess.run(['az', 'rest', '--method', 'post', '--url', f'https://management.azure.com/subscriptions/{SUB}/providers/Microsoft.CostManagement/query?api-version=2023-03-01', '--body', body, '-o', 'json'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace', shell=(os.name == 'nt'), env=dict(os.environ, MSYS_NO_PATHCONV='1'), timeout=120)
        if p.returncode != 0: return {'state': 'not read', 'tried': NOW.date().isoformat(), 'why': (p.stderr or '').strip().splitlines()[-1][:160] if p.stderr else 'no answer'}
        j = json.loads(p.stdout); rows = (j.get('properties') or {}).get('rows') or []
        if not rows: return {'state': 'not read', 'tried': NOW.date().isoformat(), 'why': 'answered with no rows'}
        return {'state': 'read', 'read_at': STAMP, 'month_to_date': f'${rows[0][0]:,.2f}', 'scope': 'the Allooloo subscription, actual cost, month to date', 'meter': 'Cost Management query API'}
    except Exception as e: return {'state': 'not read', 'tried': NOW.date().isoformat(), 'why': type(e).__name__}
txt = open(MD, encoding='utf-8').read(); m = re.search(r'```\n([\s\S]*?)```', txt); lines = [l for l in (m.group(1) if m else '').splitlines() if l.strip()]
parsed = [p for p in (parse(l) for l in lines) if p]
order = []; [order.append(p['run']) for p in parsed if p['run'] not in order]
runs = [{'run': r, 'lines': [{k: p[k] for k in ('lab', 'calls', 'tokens', 'figure', 'meter')} for p in parsed if p['run'] == r]} for r in order[-8:]]
out = {'as_of': STAMP, 'source': 'CM-KG/SPEND/SPEND.md (one line per lab per run), read nightly by the apex job; the Tavily and Azure lines from their meters', 'runs': runs,
       'tavily': tavily(sys.argv[1] if len(sys.argv) > 1 else None), 'azure': azure(), 'note': 'report only; spend never gates a run; $ as each line was written (list price where no meter)'}
json.dump(out, open(OUT, 'w', encoding='utf-8', newline='\n'), indent=1, ensure_ascii=False)
print('runs', len(runs), '· last', runs[-1]['run'] if runs else None, '· tavily', out['tavily'].get('state'), '· azure', out['azure'].get('state'), out['azure'].get('why', out['azure'].get('month_to_date', '')))
