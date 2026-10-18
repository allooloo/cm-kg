r"""SPEND.md writer (sweep close-out 2026-10-10): one line per lab per run, appended to CM-KG\SPEND\SPEND.md at the close of a sweep.
  python spend_line.py --mark <run>                  read the Tavily plan counter at sweep start -> SPEND\.tavily-start-<run>.json
  python spend_line.py <run> <since yyyy-mm-dd> [--tavily-start N] [--tavily-end N] [--only lab,lab] [--estimated] [--note text]
Lab counts are summed from the run's own fill-confirm drops (drop date >= since; no merge across older drops). Meters: Tavily = plan counter
from GET /usage (actual); ChatGPT = the batch object's usage (actual tokens; $ at batch list price); Grok = cost_in_usd_ticks on each response
(actual $). Claude, Gemini, Mistral, Perplexity = tokens from the responses, $ at list price, 'no meter'. The United States rail runs in the
East US container job; its lab calls are not visible here ('no meter'). Report only; never gates a run."""
import os, re, sys, json, glob, datetime, requests
TAVILY_CAP = 200000   # CEO 2026-10-16 (Cloudflare dashboard): Tavily plan 200,000 credits, pay-as-you-go behind it; was 100,000 here
ROOT = r'C:\ALLOOLOO'; POND = os.path.join(ROOT, 'CM-KG', 'POND'); SPEND = os.path.join(ROOT, 'CM-KG', 'SPEND'); MD = os.path.join(SPEND, 'SPEND.md')
def key(n): return open(os.path.join(ROOT, 'AGENT KEYS', n), encoding='utf-8').read().strip()
def tavily_now():
    # ORDER-026 (2026-10-16): the start marker of the 2026-10-16 sweep read 0 — a failed read must never pass as a counter of 0.
    # Three tries with backoff; raise on anything but a plan_usage figure.
    import time
    err = 'no response'
    for i in range(3):
        try:
            r = requests.get('https://api.tavily.com/usage', headers={'Authorization': 'Bearer ' + key('tavily.txt')}, timeout=30)
            j = r.json().get('account', {}) if r.status_code == 200 else {}
            if j.get('plan_usage') is not None: return int(j['plan_usage']), TAVILY_CAP
            err = f'HTTP {r.status_code}: {r.text[:120]}'
        except Exception as e: err = repr(e)[:160]
        time.sleep(20 * (i + 1))
    raise RuntimeError('Tavily /usage gave no plan_usage: ' + err)
def last_spend_reading():
    # the last "plan N of M" figure written to SPEND.md — the fallback start when a marker holds no reading
    if not os.path.exists(MD): return None
    m = re.findall(r'plan ([\d,]+) of', open(MD, encoding='utf-8').read())
    return int(m[-1].replace(',', '')) if m else None
a = sys.argv[1:]
if a[:1] == ['--mark']:
    f = os.path.join(SPEND, f'.tavily-start-{a[1]}.json')
    try: u, lim = tavily_now(); json.dump({'run': a[1], 'tavily_start': u, 'limit': lim, 'read': datetime.date.today().isoformat()}, open(f, 'w')); print('tavily start', u)
    except Exception as e: json.dump({'run': a[1], 'tavily_start': None, 'error': str(e), 'read': datetime.date.today().isoformat()}, open(f, 'w')); print('tavily start: no reading —', e)
    sys.exit()
run, since = a[0], a[1]; opt = {}
i = 2
while i < len(a):
    if a[i] in ('--tavily-start', '--tavily-end', '--only', '--note'): opt[a[i]] = a[i + 1]; i += 2
    else: opt[a[i]] = True; i += 1
only = set(opt['--only'].split(',')) if '--only' in opt else None
def drops():
    for d in glob.glob(os.path.join(POND, '*-cm-kg', 'fill-confirm', '*')):
        m = re.match(r'^(\d{4}-\d{2}-\d{2})', os.path.basename(d))
        if m and m.group(1) >= since: yield d
def rows(fn):
    for d in drops():
        p = os.path.join(d, fn)
        if os.path.exists(p):
            for l in open(p, encoding='utf-8'):
                try: yield json.loads(l)
                except Exception: pass
def tok(rs, i_k, o_k):
    n = ti = to = 0
    for r in rs:
        u = r.get('usage') or {}
        if u: n += 1; ti += int(u.get(i_k, 0) or 0); to += int(u.get(o_k, 0) or 0)
    return n, ti, to
L = []
def line(lab, calls, ti, to, usd, src):
    if only and lab.split(' ')[0] not in only: return
    est = ' (estimated)' if opt.get('--estimated') else ''
    L.append(f"{run} · {lab} · {calls} calls · {ti:,} in / {to:,} out · ${usd:,.2f} · {src}{est}")
# Grok: actual $ from cost_in_usd_ticks (1e-10 $ per tick)
gc = gi = go = ticks = 0
for d in drops():
    p = os.path.join(d, 'grok_live_usage.json')
    if os.path.exists(p):
        for u in json.load(open(p, encoding='utf-8')).get('usage') or []:
            gc += 1; gi += int(u.get('input_tokens', 0)); go += int(u.get('output_tokens', 0)); ticks += int(u.get('cost_in_usd_ticks', 0) or 0)
line('Grok (grok-4.6)', gc, gi, go, ticks / 1e10, 'meter: cost_in_usd_ticks on each response')
# ChatGPT: batch object usage (actual tokens)
bc = bi = bo = 0
for d in drops():
    p = os.path.join(d, 'openai_batch.json')
    if os.path.exists(p):
        bid = json.load(open(p))['batch']['id']
        b = requests.get(f'https://api.openai.com/v1/batches/{bid}', headers={'Authorization': 'Bearer ' + key('chatgpt.txt')}, timeout=60).json()
        bc += (b.get('request_counts') or {}).get('completed', 0); u = b.get('usage') or {}; bi += u.get('input_tokens', 0); bo += u.get('output_tokens', 0)
line('ChatGPT (gpt-4.1-mini, Batch)', bc, bi, bo, bi * 0.20 / 1e6 + bo * 0.80 / 1e6, 'meter: batch object usage; $ at batch list price')
n, ti, to = tok(rows('gemini_agm.jsonl'), 'promptTokenCount', 'candidatesTokenCount'); line('Gemini (gemini-flash-latest)', n, ti, to, ti * 0.30 / 1e6 + to * 2.50 / 1e6, 'no meter; tokens from responses, $ at list price')
n, ti, to = tok(rows('mistral_fr.jsonl'), 'prompt_tokens', 'completion_tokens'); line('Mistral (mistral-small-latest)', n, ti, to, ti * 0.10 / 1e6 + to * 0.30 / 1e6, 'no meter; tokens from responses, $ at list price')
n, ti, to = tok(rows('perplexity_pages.jsonl'), 'prompt_tokens', 'completion_tokens'); line('Perplexity (sonar-pro)', n, ti, to, n * 0.006 + ti * 3 / 1e6 + to * 15 / 1e6, 'no meter; request fee + tokens at list price')
cc = sum(len(r.get('conflicts') or []) for r in rows('rematch.jsonl'))
n, ti, to = tok(list(rows('claude_isin.jsonl')) + list(rows('claude_auditor.jsonl')), 'input_tokens', 'output_tokens')
line('Claude (claude-sonnet-5)', n + cc, ti, to, ti * 3 / 1e6 + to * 15 / 1e6, 'no meter; rematch collision calls counted, not token-metered')
if not only or 'Tavily' in only:
    st = opt.get('--tavily-start')
    note_t = ''
    if st is None:
        f = os.path.join(SPEND, f'.tavily-start-{run}.json'); st = json.load(open(f))['tavily_start'] if os.path.exists(f) else None
        if not st:   # None or 0 = the marker held no reading (ORDER-026): fall back to the last reading in SPEND.md, said so
            st = last_spend_reading(); note_t = ' (estimated: start marker had no reading; start taken from the last SPEND.md reading' + (f' {st:,}' if st else '') + ')'
    if '--tavily-end' in opt: en, lim = int(opt['--tavily-end']), TAVILY_CAP
    else: en, lim = tavily_now()
    used = f'{en - int(st):,} credits used' if st else 'credits used: no start reading'
    L.append(f"{run} · Tavily · {used} · plan {en:,} of {lim:,}, {lim - en:,} remaining · meter: GET /usage plan counter" + (' (estimated)' if opt.get('--estimated') else '') + note_t)
if not only or 'United' in only:
    L.append(f"{run} · United States job (EDGAR, Gemini, Perplexity) · no meter · lab calls run in the East US container job and are not counted here")
if '--note' in opt: L = [l + ' · ' + opt['--note'] for l in L]
if not os.path.exists(MD):
    open(MD, 'w', encoding='utf-8').write('# SPEND — one line per lab per sweep run\n\n`run · lab · calls · tokens · $ · meter`\n\nWritten at the close of each sweep by CM-KG/RAILS/spend_line.py (close-out 2026-10-10). Report only; never gates a run.\n\n```\n```\n')
s = open(MD, encoding='utf-8').read(); k = s.rfind('```')
open(MD, 'w', encoding='utf-8').write(s[:k] + ''.join(l + '\n' for l in L) + s[k:])
print('\n'.join(L))
