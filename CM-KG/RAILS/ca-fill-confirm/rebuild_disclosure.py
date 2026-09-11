"""Rebuilds CM-KG\DISCLOSURE\ca-disclosure.xlsx and ca-events.jsonl with passes 2 and 3 applied:
  + alias-rematch events (Tavily + alias, adjudicated by Claude on collisions)
  + Gemini AGM / record-date findings as agm_record_date events
  + ChatGPT batch columns on financial_statement rows (period end, statement date, auditor named, going concern, read by ChatGPT (batch))
  + Mistral (fr) columns on French releases
  + a State column on every event: sourced (one read) · confirmed (a second copy on another wire or a bulletin on the same date) · filled (lab-added)
  + Method tab listing all eight engines with duty and count. Keeps the Width 1 workbook as ca-disclosure-width1.xlsx."""
import shutil, hashlib
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from fc_common import *
from collections import Counter, defaultdict
from common import event, classify, in_window
XL = r'C:\ALLOOLOO\CM-KG\DISCLOSURE\ca-disclosure.xlsx'; BAK = XL.replace('ca-disclosure.xlsx', 'ca-disclosure-width1.xlsx')
JL = EVENTS_JSONL; JBAK = JL.replace('ca-events.jsonl', 'ca-events-width1.jsonl')
if not os.path.exists(BAK): shutil.copy(XL, BAK)
if not os.path.exists(JBAK): shutil.copy(JL, JBAK)
issuers = load_issuers(); byk = {key(r): r for r in issuers}
EV = jload(JBAK)
for e in EV: e['state'] = 'sourced'; e['pass'] = 'width1'
touched = Counter()
# alias rematch events
for d in jload('raw/rematch.jsonl'):
    for e in d.get('events', []): e['state'] = 'filled'; e['pass'] = 'fill:alias'; EV.append(e); touched['Tavily + alias'] += 1
    for c in d.get('conflicts', []): touched['Claude alias adjudications'] += 1
# Gemini AGM findings
for d in jload('raw/gemini_agm.jsonl'):
    r = byk.get(d['key'])
    for f in d.get('findings', []) if r else []:
        rd = to_iso(f.get('release_date', '')); sd = to_iso(f.get('stated_date', '')); u = f.get('release_url', '')
        if not (rd and u.startswith('http') and in_window(rd)): continue
        e = event(r, 'agm_record_date', rd, f"[{f.get('kind', '')}] stated date {sd}: " + (f.get('evidence') or '')[:200], wire_of(u), u, 'read by Gemini', wire=wire_of(u), detail=f"stated {f.get('kind')} date {sd}")
        e['state'] = 'filled'; e['pass'] = 'fill:gemini'; EV.append(e); touched['Gemini'] += 1
# ChatGPT + Mistral columns
gpt = {d['url']: d for d in jload('raw/chatgpt_extract.jsonl') if d.get('url')}
mis = {d['url']: d for d in jload('raw/mistral_fr.jsonl')}
# dedupe on the standing key
seen = {}
for e in EV:
    kk = (e['exchange'], e['ticker'], e['event_type'], e['date'], e['url'].lower().rstrip('/'))
    if kk not in seen: seen[kk] = e
EV = sorted(seen.values(), key=lambda e: (e['exchange'], e['ticker'], e['date'], e['event_type']))
# confirm: a second copy on another wire, or a bulletin on the same date, for financial_statement and agm_record_date rows
by_iss_date = defaultdict(list)
for e in EV: by_iss_date[(e['exchange'], e['ticker'], e['date'])].append(e)
def tkey(t): return ' '.join(norm(t).split()[:8])
conf_n = 0
for e in EV:
    if e['event_type'] not in ('financial_statement', 'agm_record_date'): continue
    others = [o for o in by_iss_date[(e['exchange'], e['ticker'], e['date'])] if o is not e]
    second = None
    for o in others:
        if o['event_type'] in ('exchange_bulletin', 'corporate_action', 'halt_resume') and 'bulletin' in o['source'].lower(): second = o; break
        if o.get('wire') and o.get('wire') != e.get('wire') and tkey(o['title']) == tkey(e['title']): second = o; break
        if o['read_by'] != e['read_by'] and o['url'].lower().rstrip('/') != e['url'].lower().rstrip('/') and tkey(o['title']) == tkey(e['title']): second = o; break
    if second: e['state'] = 'confirmed'; e['second_source'] = second['url']; e['second_read_by'] = second['read_by']; conf_n += 1
# lab columns
for e in EV:
    g = gpt.get(e['url']); m = mis.get(e['url'])
    if g and not g.get('error'):
        e['period_end'] = g.get('period_end', ''); e['statement_date'] = g.get('statement_date', ''); e['auditor_named'] = g.get('auditor_named', ''); e['going_concern'] = g.get('going_concern', ''); e['extract_evidence'] = g.get('evidence', ''); e['extract_read_by'] = 'read by ChatGPT (batch)'
        touched['ChatGPT (batch)'] += sum(1 for x in ('period_end', 'statement_date', 'auditor_named', 'going_concern') if g.get(x))
    if m and not m.get('error'):
        for x in ('period_end', 'statement_date', 'auditor_named', 'going_concern'):
            if m.get(x): e[x] = m[x]; touched['Mistral (fr)'] += 1
        if m.get('meeting_date') or m.get('record_date'): e['detail'] = (e.get('detail') or '') + f" [fr: meeting {m.get('meeting_date')} record {m.get('record_date')}]"; touched['Mistral (fr)'] += 1
        e['extract_evidence'] = m.get('evidence', ''); e['extract_read_by'] = ('read by Mistral (fr)' + (' + ChatGPT (batch)' if g else ''))
# jsonl
with open(JL, 'w', encoding='utf-8') as f:
    for e in EV: f.write(json.dumps({**e, 'as_of': TODAY.isoformat(), 'node': 'ca-cm-kg', 'width': 1}, ensure_ascii=False) + '\n')
# workbook
wb = Workbook(); wb.remove(wb.active)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
_ILLEGAL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
def clean_cell(v): return _ILLEGAL.sub('', v) if isinstance(v, str) else v
def sheet(name, cols, rows, widths):
    ws = wb.create_sheet(name); ws.append(cols)
    for c in ws[1]: c.font = BOLD; c.fill = HFILL; c.alignment = Alignment(wrap_text=True, vertical='top')
    for r in rows: ws.append([clean_cell(v) for v in r])
    for row in ws.iter_rows(min_row=2):
        for c in row: c.font = ARIAL
    ws.freeze_panes = 'A2'; ws.auto_filter.ref = f'A1:{get_column_letter(len(cols))}{max(len(rows) + 1, 2)}'
    for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
    return ws
ECOLS = ['Exchange', 'Ticker', 'ISIN', 'LEI', 'Issuer', 'Event type', 'Date', 'Title', 'Wire', 'Source', 'URL', 'Read by', 'Detail', 'State', 'Second source', 'Second read by', 'Period end', 'Statement date', 'Auditor named', 'Going concern', 'Extract evidence', 'Extract read by', 'Pass']
erows = [[e['exchange'], e['ticker'], e['isin'], e['lei'], e['issuer'], e['event_type'], e['date'], e['title'], e['wire'], e['source'], e['url'], e['read_by'], e.get('detail', ''), e['state'], e.get('second_source', ''), e.get('second_read_by', ''), e.get('period_end', ''), e.get('statement_date', ''), e.get('auditor_named', ''), e.get('going_concern', ''), e.get('extract_evidence', ''), e.get('extract_read_by', ''), e.get('pass', '')] for e in EV]
sheet('Events', ECOLS, erows, [12, 10, 15, 22, 34, 18, 11, 60, 18, 24, 60, 40, 30, 11, 50, 30, 12, 12, 28, 10, 60, 24, 12])
per = Counter((e['exchange'], e['ticker']) for e in EV); by_type = defaultdict(Counter)
for e in EV: by_type[(e['exchange'], e['ticker'])][e['event_type']] += 1
TYPES = ['newswire_release', 'financial_statement', 'agm_record_date', 'early_warning', 'corporate_action', 'halt_resume', 'exchange_bulletin']
n_ev = len(EV) + 1; crows = []
for r in issuers:
    k = (r['exchange'], r['ticker']); i = len(crows) + 2
    crows.append([r['exchange'], r['ticker'], r['isin'], r['name'], r['wire'], f"=COUNTIFS(Events!$A$2:$A${n_ev},A{i},Events!$B$2:$B${n_ev},B{i})", per.get(k, 0)] + [by_type[k].get(t, 0) for t in TYPES] + [f'=IF(F{i}=0,1,0)', f"=COUNTIFS(Events!$A$2:$A${n_ev},A{i},Events!$B$2:$B${n_ev},B{i},Events!$N$2:$N${n_ev},\"confirmed\")"])
cv = sheet('Coverage', ['Exchange', 'Ticker', 'ISIN', 'Issuer', 'Newswire of habit', 'Events (live)', 'Events (built)'] + TYPES + ['Zero events (live)', 'Confirmed events (live)'], crows, [12, 10, 15, 34, 20, 12, 12] + [14] * len(TYPES) + [12, 14])
cv.append([]); cv.append(['TOTAL', '', '', '', '', f'=SUM(F2:F{len(crows) + 1})', f'=SUM(G2:G{len(crows) + 1})'] + [f'=SUM({get_column_letter(8 + j)}2:{get_column_letter(8 + j)}{len(crows) + 1})' for j in range(len(TYPES) + 2)])
for c in cv[cv.max_row]: c.font = BOLD
# Gaps: carry Width 1 gaps, drop ambiguous rows now resolved, add adjudication blanks
from openpyxl import load_workbook
g1 = load_workbook(BAK, read_only=True)['Gaps']; have = set((e['exchange'], e['ticker']) for e in EV)
grows = []
for row in g1.iter_rows(min_row=2, values_only=True):
    if not row or not row[0] or row[0] == 'TOTAL gap rows': continue
    if row[3] == 'coverage' and (row[0], row[1]) in have: continue
    grows.append(list(row))
for d in jload('raw/rematch.jsonl'):
    for c in d.get('conflicts', []):
        if not c.get('ruling'): grows.append([d['key'].split('|')[0], d['key'].split('|')[1], byk.get(d['key'], {}).get('name', ''), 'alias collision', f"{c['title'][:80]} | alias '{c['alias']}' shared with {', '.join(c['other_issuers'])} | adjudicated by Claude: left out — {c.get('reason', '')[:120]}"])
zero = [r for r in issuers if (r['exchange'], r['ticker']) not in have]
gs = sheet('Gaps', ['Exchange', 'Ticker', 'Issuer', 'Worker / field', 'Reason'], grows, [12, 10, 34, 24, 110]); gs.append([]); gs.append(['TOTAL gap rows', '', '', '', f'=COUNTA(E2:E{len(grows) + 1})'])
# Method: eight engines
bat = json.load(open('raw/openai_batch_usage.json')) if os.path.exists('raw/openai_batch_usage.json') else {}
gem = jload('raw/gemini_agm.jsonl'); mis_rows = jload('raw/mistral_fr.jsonl'); rem = jload('raw/rematch.jsonl')
METHOD = [('Passes 2 and 3 (ORDER-004, ' + TODAY.isoformat() + ')', 'Engine duty and count of fields touched on Canada'),
          ('Claude (claude-sonnet-5)', f"Adjudicated alias collisions in the rematch: {touched['Claude alias adjudications']} titles ruled. Adjudication of Width 0 ISIN/auditor conflicts is on the issuer workbook."),
          ('ChatGPT (gpt-4.1-mini via the Batch API, strict JSON schema)', f"One batch of {bat.get('n', len(gpt))} financial_statement releases (bodies fetched; Newsfile and Business Wire bodies mostly unavailable): {touched['ChatGPT (batch)']} field values written (period end, statement date, auditor named, going concern). Tokens: {bat.get('usage', {})}. Label 'read by ChatGPT (batch)'."),
          ('Google Gemini (gemini-flash-latest, long context)', f"Read {len(gem)} issuers' 12-month release sets (full bodies where fetched, titles otherwise) for issuers with no AGM/record-date event: {touched['Gemini']} agm_record_date events added, each citing the release. Label 'read by Gemini'."),
          ('Perplexity (sonar-pro)', 'Touched nothing on the Disclosure workbook directly; its recovered wire pages feed the alias rematch and the issuer record.'),
          ('Grok (grok-4.6, Responses API + web/X search)', 'Wired into the daily refresh as the 48-hour live layer (grok_live.py) from 2026-09-11; validated on one TSXV halt query on 2026-09-10 (7 items, 6 matched to the roster); no events written for the backfill.'),
          ('Mistral (mistral-small-latest)', f"Read {len(mis_rows)} French-language releases ({sum(1 for m in mis_rows if m.get('has_body'))} with full text): {touched['Mistral (fr)']} field values written. Label 'read by Mistral (fr)'."),
          ('Tavily (search)', f"Alias rematch for {len(rem)} zero-event / ambiguous issuers: {touched['Tavily + alias']} events added via legal name or sourced alias."),
          ('Cloudflare', 'Touched nothing on the Disclosure workbook.'),
          ('States', f"sourced = one read (Width 1); filled = lab-added (alias rematch, Gemini); confirmed = a second copy of the same release on another wire, or an exchange bulletin, on the same date — {conf_n} events confirmed. Second source and its read-by are on the row.")]
mt = sheet('Method', ['Item', 'Detail'], [list(m) for m in METHOD], [34, 150])
for row in mt.iter_rows(min_row=2):
    for c in row: c.alignment = Alignment(wrap_text=True, vertical='top')
wb.save(XL)
import pond, shutil as _sh; _ad = pond.assembled('ca-cm-kg'); _sh.copy(XL, os.path.join(_ad, 'ca-disclosure.xlsx')); _sh.copy(JL, os.path.join(_ad, 'ca-events.jsonl')); print('versioned copy', _ad)  # pond rule 2
print('saved', XL, JL); print('events', len(EV), 'confirmed', conf_n, 'touched', dict(touched)); print('by state', Counter(e['state'] for e in EV)); print('issuers with events', len(per), '/', len(issuers), 'zero', len(zero))
print('zero first 20', [f"{r['exchange']}:{r['ticker']} {r['name']}" for r in zero[:20]])
