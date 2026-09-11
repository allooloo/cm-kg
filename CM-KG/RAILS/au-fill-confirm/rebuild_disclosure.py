r"""Rebuilds CM-KG\DISCLOSURE\au-disclosure.xlsx and events\au-events.jsonl with passes 2 and 3: rematch events, Gemini AGM / record-date findings,
ChatGPT Appendix 4E/4D reads (period end, statement date) in Detail, Mistral reads, and a State per event: sourced · confirmed (results / AGM rows
seen on a second source family — ASX vs annual report vs wire — within 45 days) · filled. The Width 1 workbook is kept beside it as
au-disclosure-width1.xlsx (+ au-events-width1.jsonl); a versioned copy lands in the pond."""
import shutil, hashlib
from fc_common import *
from collections import Counter, defaultdict
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
X = r'C:\ALLOOLOO\CM-KG\DISCLOSURE\au-disclosure.xlsx'; J = r'C:\ALLOOLOO\CM-KG\DISCLOSURE\events\au-events.jsonl'
BX = X.replace('au-disclosure.xlsx', 'au-disclosure-width1.xlsx'); BJ = J.replace('au-events.jsonl', 'au-events-width1.jsonl')
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
rep = {}
for d in jload('raw/chatgpt_reports.jsonl'):
    if d.get('custom_id'): rep[d['custom_id']] = d
mis = {d['url']: d for d in jload('raw/mistral_reads.jsonl')}
events_all = base + new
for e in events_all:
    for kk in ('key', 'as_of', 'node', 'width'): e.pop(kk, None)
    m = re.search(r'idsId=(\d+)', e.get('url', '')); x = rep.get(m.group(1)) if m else None
    if x and e['event_type'] == 'financial_statement' and not x.get('error'):
        bits = [b for b in [f"period_end {x.get('period_end')}" if x.get('period_end') else '', f"statement_date {x.get('statement_date')}" if x.get('statement_date') else '', f"auditor {x.get('auditor')}" if x.get('auditor') else '', 'going-concern material uncertainty' if x.get('going_concern') == 'material_uncertainty' else ''] if b]
        if bits: e['detail'] = (e.get('detail', '') + '; ' if e.get('detail') else '') + 'read by ChatGPT (batch): ' + ', '.join(bits); e['read_by'] += ' · read by ChatGPT (batch)'
    mm = mis.get(e['url'])
    if mm and not mm.get('error') and (mm.get('period_end') or mm.get('meeting_date') or mm.get('record_date')):
        e['detail'] = (e.get('detail', '') + '; ' if e.get('detail') else '') + 'read by Mistral: ' + ', '.join(f'{k} {mm[k]}' for k in ('period_end', 'meeting_date', 'record_date', 'auditor') if mm.get(k)); e['read_by'] += ' · read by Mistral'
seen = {}
for e in sorted(events_all, key=lambda e: 0 if e.get('state') == 'sourced' else 1):
    kk = (e['exchange'], e['ticker'], e['event_type'], e['date'], e['url'].lower().rstrip('/'))
    if kk not in seen: seen[kk] = e
events_all = list(seen.values())
by_iss = defaultdict(list)
for e in events_all: by_iss[(e['exchange'], e['ticker'])].append(e)
def fam(e):
    rb = e['read_by']
    if 'asx.com.au' in rb or 'nsx.com.au' in rb: return 'exchange'
    if 'ASIC' in rb: return 'registry'
    if 'Gemini' in rb or 'ChatGPT' in rb: return 'document'
    return 'wire'
conf_n = 0
for k, evs in by_iss.items():
    for e in evs:
        if e['event_type'] not in ('financial_statement', 'agm_record_date'): continue
        for o in evs:
            if o is e or fam(o) == fam(e) or o['event_type'] != e['event_type']: continue
            try: gap = abs((datetime.date.fromisoformat(e['date']) - datetime.date.fromisoformat(o['date'])).days)
            except Exception: continue
            if gap <= 45: e['state'] = 'confirmed'; e['detail'] = (e.get('detail', '') + '; ' if e.get('detail') else '') + f"confirmed by {o['source']} {o['date']} {o['url']}"; conf_n += 1; break
events_all.sort(key=lambda e: (e['exchange'], e['ticker'], e['date'], e['event_type']))
with open(J, 'w', encoding='utf-8') as f:
    for e in events_all: f.write(json.dumps({**e, 'as_of': TODAY.isoformat(), 'node': NODE, 'width': 1}, ensure_ascii=False) + '\n')
wb = load_workbook(BX); ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True)
ws = wb['Events']; ws.delete_rows(2, ws.max_row); CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
for e in events_all:
    ws.append([CTRL.sub('', str(v)) if isinstance(v, str) else v for v in [e['exchange'], e['ticker'], e['isin'], e['lei'], e['issuer'], e['event_type'], e['date'], e['title'], e.get('asx_category', ''), e.get('price_sensitive', ''), e['wire'], e['source'], e['url'], e['read_by'], e['detail'], e.get('state', 'sourced')]])
for row in ws.iter_rows(min_row=2):
    for c in row: c.font = ARIAL
ws.auto_filter.ref = f'A1:{get_column_letter(16)}{len(events_all) + 1}'
cv = wb['Coverage']; hdr = [c.value for c in cv[1]]; Hc = {h: i + 1 for i, h in enumerate(hdr)}
per = Counter((e['exchange'], e['ticker']) for e in events_all); by_type = defaultdict(Counter)
for e in events_all: by_type[(e['exchange'], e['ticker'])][e['event_type']] += 1
n_ev = len(events_all) + 1
for rr in range(2, cv.max_row + 1):
    ex = cv.cell(row=rr, column=Hc['Exchange']).value; t = cv.cell(row=rr, column=Hc['Code']).value
    if not ex or ex == 'TOTAL': continue
    cv.cell(row=rr, column=Hc['Events (live)']).value = f"=COUNTIFS(Events!$A$2:$A${n_ev},A{rr},Events!$B$2:$B${n_ev},B{rr})"; cv.cell(row=rr, column=Hc['Events (built)']).value = per.get((ex, t), 0)
    for h in hdr:
        if h in Hc and h in by_type[(ex, t)]: cv.cell(row=rr, column=Hc[h]).value = by_type[(ex, t)].get(h, 0)
mt = wb['Method']; mt.append([]); mt.append(['Passes 2 and 3 (ORDER-012, ' + TODAY.isoformat() + ')', 'Engine duty and count on the Australia Disclosure workbook'])
for c in mt[mt.max_row]: c.font = BOLD
rm = jload('raw/rematch.jsonl'); rm_ev = sum(len(d.get('events', [])) for d in rm); rm_conf = sum(len(d.get('conflicts', [])) for d in rm)
ur = json.load(open('raw/chatgpt_reports_usage.json')) if os.path.exists('raw/chatgpt_reports_usage.json') else {}; mc = json.load(open('raw/mistral_count.json')) if os.path.exists('raw/mistral_count.json') else {}; gl = json.load(open('raw/grok_live_usage.json')) if os.path.exists('raw/grok_live_usage.json') else {}
for a, b in [('Claude (claude-sonnet-5)', f'Rematch collisions ruled from the release text: {rm_conf}. Label "adjudicated by Claude".'),
             ('ChatGPT (gpt-4.1-mini, Batch API)', f"Read {ur.get('n', 0)} ASX-lodged documents; Appendix 4E/4D period end and statement date written to Detail. Label 'read by ChatGPT (batch)'."),
             ('Google Gemini (gemini-flash-latest)', f'AGM / general-meeting / record dates stated in the announcement set: {gem_n} events written (dated on the announcement, stated date in Detail). Label "read by Gemini".'),
             ('Perplexity (Agent API, preset low)', f"Located company pages: {sum(1 for d in jload('raw/perplexity_pages.jsonl') if d.get('verified'))} verified; page titles became sourced aliases used by the rematch."),
             ('Grok (grok-4.6)', f"Live layer wired into the weekly refresh; validation run found {gl.get('halts', 0)} halt/suspension/reinstatement items and {gl.get('newswire', 0)} silent-issuer items."),
             ('Mistral (mistral-small-latest)', f"Non-English announcements found: {mc.get('n_targets', 0)}; read {mc.get('n_targets', 0)}."),
             ('Tavily (search)', f'Rematch on legal name OR sourced alias for zero-event and ambiguous issuers: {len(rm)} issuers searched, {rm_ev} events added.'),
             ('Cloudflare', 'Not used on this workbook.'),
             ('State', f'sourced = one source; filled = lab-derived row; confirmed = results / AGM rows seen on a second source family (exchange vs document vs wire) within 45 days: {conf_n} events confirmed.')]:
    mt.append([a, b])
    for c in mt[mt.max_row]: c.font = ARIAL; c.alignment = Alignment(wrap_text=True, vertical='top')
wb.save(X); _ad = pond.assembled(NODE); shutil.copy(X, os.path.join(_ad, 'au-disclosure.xlsx')); shutil.copy(J, os.path.join(_ad, 'au-events.jsonl'))
print('saved', X, 'events', len(events_all), 'new from passes', len(new), 'gemini', gem_n, 'confirmed', conf_n, 'rematch events', rm_ev, 'collisions', rm_conf, '| versioned copy', _ad)
print('by state', Counter(e.get('state') for e in events_all))
