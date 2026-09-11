r"""Rebuilds CM-KG\DISCLOSURE\uk-disclosure.xlsx and events\uk-events.jsonl with passes 2 and 3: rematch events (alias-matched, Claude-adjudicated
collisions), Gemini AGM / record-date findings, ChatGPT results reads (period end, statement date, auditor named, going concern) in Detail, Mistral
reads, and a State per event: sourced (one source) · confirmed (results / AGM rows seen on a second source — RNS vs Companies House accounts filing
vs wire — within 45 days) · filled (lab-derived row). The Width 1 workbook is kept beside it as uk-disclosure-width1.xlsx (+ uk-events-width1.jsonl)."""
import shutil, hashlib, subprocess
from fc_common import *
from collections import Counter, defaultdict
X = r'C:\ALLOOLOO\CM-KG\DISCLOSURE\uk-disclosure.xlsx'; J = EVENTS_JSONL
BX = X.replace('uk-disclosure.xlsx', 'uk-disclosure-width1.xlsx'); BJ = J.replace('uk-events.jsonl', 'uk-events-width1.jsonl')
if not os.path.exists(BX): shutil.copy(X, BX)
if not os.path.exists(BJ): shutil.copy(J, BJ)
issuers = load_issuers(); byk = {key(r): r for r in issuers}
base = [json.loads(l) for l in open(BJ, encoding='utf-8')]
for e in base: e.setdefault('state', 'sourced')
new = []
for d in jload('raw/rematch.jsonl'):
    for e in d.get('events', []): e['state'] = 'sourced'; new.append(e)
gem_n = 0
for d in jload('raw/gemini_agm.jsonl'):
    r = byk.get(d['key'])
    if not r: continue
    for f in d.get('findings', []):
        u = f.get('release_url', ''); rd = to_iso(f.get('release_date', '')); sd = to_iso(f.get('stated_date', ''))
        if not (u.startswith('http') and rd and sd): continue
        new.append({**event(r, 'agm_record_date', rd, f"{f.get('kind', 'meeting')} date stated: {sd}", 'issuer announcement (read by Gemini)', u, 'read by Gemini', detail=f"stated {f.get('kind')} date {sd}; evidence: {(f.get('evidence') or '')[:200]}"), 'state': 'filled'}); gem_n += 1
res_by_url = {}
for d in jload('raw/chatgpt_results.jsonl'):
    if d.get('custom_id'): res_by_url[d['custom_id']] = d
mis_by_url = {d['url']: d for d in jload('raw/mistral_reads.jsonl')}
events_all = base + new
for e in events_all:
    e.pop('key', None); e.pop('as_of', None); e.pop('node', None); e.pop('width', None)
    cid = hashlib.sha1(e['url'].encode()).hexdigest()[:24]
    x = res_by_url.get(cid)
    if x and e['event_type'] == 'financial_statement' and not x.get('error'):
        bits = [f"period_end {x.get('period_end')}" if x.get('period_end') else '', f"statement_date {x.get('statement_date')}" if x.get('statement_date') else '', f"auditor named {x.get('auditor_named')}" if x.get('auditor_named') else '', 'going-concern language' if x.get('going_concern') == 'yes' else '']
        bits = [b for b in bits if b]
        if bits: e['detail'] = (e['detail'] + '; ' if e.get('detail') else '') + 'read by ChatGPT (batch): ' + ', '.join(bits); e['read_by'] = e['read_by'] + ' · read by ChatGPT (batch)'
    m = mis_by_url.get(e['url'])
    if m and not m.get('error') and (m.get('period_end') or m.get('meeting_date') or m.get('record_date')):
        e['detail'] = (e['detail'] + '; ' if e.get('detail') else '') + 'read by Mistral: ' + ', '.join(f'{k} {m[k]}' for k in ('period_end', 'meeting_date', 'record_date', 'auditor') if m.get(k)); e['read_by'] += ' · read by Mistral'
# dedupe
seen = {}
for e in sorted(events_all, key=lambda e: 0 if e.get('state') == 'sourced' else 1):
    kk = (e['exchange'], e['ticker'], e['event_type'], e['date'], e['url'].lower().rstrip('/'))
    if kk not in seen: seen[kk] = e
events_all = list(seen.values())
# Pass 3 confirm: results / AGM rows confirmed across sources within 45 days
by_iss = defaultdict(list)
for e in events_all: by_iss[(e['exchange'], e['ticker'])].append(e)
def srcfam(e):
    rb = e['read_by']
    if 'Companies House' in rb: return 'registry'
    if 'investegate' in rb or 'aquis.eu' in rb or e.get('wire', '').startswith('RNS'): return 'rns'
    return 'wire'
conf_n = 0
for k, evs in by_iss.items():
    for e in evs:
        if e['event_type'] not in ('financial_statement', 'agm_record_date', 'ch_accounts_filed'): continue
        fam = srcfam(e)
        for o in evs:
            if o is e or srcfam(o) == fam: continue
            if e['event_type'] == 'financial_statement' and o['event_type'] not in ('financial_statement', 'ch_accounts_filed'): continue
            if e['event_type'] == 'agm_record_date' and o['event_type'] not in ('agm_record_date', 'ch_resolution'): continue
            if e['event_type'] == 'ch_accounts_filed' and o['event_type'] != 'financial_statement': continue
            try: gap = abs((datetime.date.fromisoformat(e['date']) - datetime.date.fromisoformat(o['date'])).days)
            except Exception: continue
            if gap <= 45:
                e['state'] = 'confirmed'; e['detail'] = (e.get('detail', '') + '; ' if e.get('detail') else '') + f"confirmed by {o['source']} {o['date']} {o['url']}"; conf_n += 1; break
events_all.sort(key=lambda e: (e['exchange'], e['ticker'], e['date'], e['event_type']))
with open(J, 'w', encoding='utf-8') as f:
    for e in events_all: f.write(json.dumps({**e, 'as_of': TODAY.isoformat(), 'node': 'uk-cm-kg', 'width': 1}, ensure_ascii=False) + '\n')
# workbook: re-run the Width 1 assembler's sheet layout on the merged set by writing the merged jsonl next to it and rebuilding the Events sheet
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
wb = load_workbook(BX)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
ws = wb['Events']; ws.delete_rows(2, ws.max_row)
ECOLS = [c.value for c in ws[1]]
CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
for e in events_all:
    ws.append([CTRL.sub('', str(v)) if isinstance(v, str) else v for v in [e['exchange'], e['ticker'], e['isin'], e['lei'], e['issuer'], e['event_type'], e['date'], e['title'], e.get('rns_category', ''), e.get('ch_filing_type', ''), e['wire'], e['source'], e['url'], e['read_by'], e['detail'], e.get('state', 'sourced')]])
for row in ws.iter_rows(min_row=2):
    for c in row: c.font = ARIAL
ws.auto_filter.ref = f'A1:{get_column_letter(len(ECOLS))}{len(events_all) + 1}'
# Coverage 'Events (built)' and type counts refresh
cv = wb['Coverage']; hdr = [c.value for c in cv[1]]; Hc = {h: i + 1 for i, h in enumerate(hdr)}
per = Counter((e['exchange'], e['ticker']) for e in events_all); by_type = defaultdict(Counter)
for e in events_all: by_type[(e['exchange'], e['ticker'])][e['event_type']] += 1
n_ev = len(events_all) + 1
for rr in range(2, cv.max_row + 1):
    ex = cv.cell(row=rr, column=Hc['Exchange']).value; t = cv.cell(row=rr, column=Hc['Ticker']).value
    if not ex or ex == 'TOTAL': continue
    cv.cell(row=rr, column=Hc['Events (live)']).value = f"=COUNTIFS(Events!$A$2:$A${n_ev},A{rr},Events!$B$2:$B${n_ev},B{rr})"
    cv.cell(row=rr, column=Hc['Events (built)']).value = per.get((ex, t), 0)
    for h in hdr:
        if h and h in by_type[(ex, t)] or (h or '').startswith(('regulatory_', 'financial_', 'agm_', 'director_', 'early_', 'corporate_', 'halt_', 'newswire_', 'ch_')):
            if h in Hc: cv.cell(row=rr, column=Hc[h]).value = by_type[(ex, t)].get(h, 0)
# Method additions
mt = wb['Method']; mt.append([]); mt.append(['Passes 2 and 3 (ORDER-009, ' + TODAY.isoformat() + ')', 'Engine duty and count on the United Kingdom Disclosure workbook'])
for c in mt[mt.max_row]: c.font = BOLD
rm = jload('raw/rematch.jsonl'); rm_ev = sum(len(d.get('events', [])) for d in rm); rm_conf = sum(len(d.get('conflicts', [])) for d in rm)
ur = json.load(open('raw/chatgpt_results_usage.json')) if os.path.exists('raw/chatgpt_results_usage.json') else {}
mc = json.load(open('raw/mistral_count.json')) if os.path.exists('raw/mistral_count.json') else {}
gl = json.load(open('raw/grok_live_usage.json')) if os.path.exists('raw/grok_live_usage.json') else {}
rows_m = [('Claude (claude-sonnet-5)', f'Rematch collisions (a headline matching two roster issuers): {rm_conf} ruled from the release text. Label "adjudicated by Claude".'),
          ('ChatGPT (gpt-4.1-mini, Batch API)', f"Read {ur.get('n', 0)} financial_statement announcements (Investegate text): period end, statement date, auditor named, going-concern language written to Detail. Label 'read by ChatGPT (batch)'."),
          ('Google Gemini (gemini-flash-latest)', f'AGM / general-meeting / record dates stated in the 12-month RNS set: {gem_n} events written (dated on the announcement, stated date in Detail). Label "read by Gemini".'),
          ('Perplexity', f"Located regulatory-news pages for issuers with a missing/empty Investegate page: {sum(1 for d in jload('raw/perplexity_pages.jsonl') if d.get('verified'))} verified; page display names became sourced aliases used by the rematch. This run: sonar-pro, label 'read by Perplexity (agent)'. From ORDER-010 Part B: Agent API presets low / fast, label 'read by Perplexity (agent · low/fast)'; Sonar Chat Completions retire 2026-09-27."),
          ('Grok (grok-4.6)', f"Live layer wired into the weekly refresh; validation run found {gl.get('halts', 0)} suspension/restoration items and {gl.get('newswire', 0)} silent-issuer items. Label 'read by Grok (live)'."),
          ('Mistral (mistral-small-latest)', f"Non-English announcements found: {mc.get('n_targets', 0)}; read {mc.get('n_targets', 0)}. Label 'read by Mistral'."),
          ('Tavily (search)', f'Rematch on legal name OR sourced alias for zero-event and ambiguous issuers: {len(rm)} issuers searched, {rm_ev} events added.'),
          ('Cloudflare', 'Not used on this workbook.'),
          ('State', f'sourced = one source; filled = lab-derived row; confirmed = results / AGM / accounts rows seen on a second source family (RNS vs Companies House vs wire) within 45 days: {conf_n} events confirmed.')]
for a, b in rows_m:
    mt.append([a, b])
    for c in mt[mt.max_row]: c.font = ARIAL; c.alignment = Alignment(wrap_text=True, vertical='top')
wb.save(X)
import pond; _ad = pond.assembled('uk-cm-kg'); shutil.copy(X, os.path.join(_ad, 'uk-disclosure.xlsx')); shutil.copy(J, os.path.join(_ad, 'uk-events.jsonl'))  # pond rule 2: versioned outputs
print('saved', X, 'events', len(events_all), 'new from passes', len(new), 'gemini', gem_n, 'confirmed', conf_n, 'rematch events', rm_ev, 'collisions', rm_conf, '| versioned copy', _ad)
print('by state', Counter(e.get('state') for e in events_all))
