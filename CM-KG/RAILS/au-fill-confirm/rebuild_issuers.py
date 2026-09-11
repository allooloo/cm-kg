r"""Rebuilds CM-KG\ISSUERS\au-issuers.xlsx with passes 2 and 3 applied: 'Also known as' (+ source, read by); Claude rulings written into LEI / ACN where the
cell was blank or in conflict; ChatGPT annual-report reads written into Auditor / Share registry where blank, plus 'Accounts period end' and 'Going concern
(annual report)'; Gemini registry reads where blank; per-field State columns updated with second source and second read-by; a summary State column; Method
tab listing all eight engines with the exact duty and count on Australia. The Width 0 workbook is kept beside it as au-issuers-width0.xlsx; a versioned copy
lands in POND\au-cm-kg\assembled\<date>\."""
import shutil
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from fc_common import *
from collections import Counter
SRC = r'C:\ALLOOLOO\CM-KG\ISSUERS\au-issuers.xlsx'; BAK = SRC.replace('au-issuers.xlsx', 'au-issuers-width0.xlsx')
if not os.path.exists(BAK): shutil.copy(SRC, BAK)
wb = load_workbook(BAK)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
CTRL0 = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
def _clean(o):
    if isinstance(o, str): return CTRL0.sub('', o)
    if isinstance(o, dict): return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, list): return [_clean(v) for v in o]
    return o
conf = _clean({d['key']: d for d in jload('raw/confirm_fields.jsonl')}); ALIASES = _clean(all_aliases())
claude_lei = _clean({d['key']: d for d in jload('raw/claude_lei.jsonl')}); claude_acn = _clean({d['key']: d for d in jload('raw/claude_acn.jsonl')})
rulings = _clean({d['key']: d for d in jload('raw/conflict_rulings.jsonl')}); gem = _clean({d['key']: d for d in jload('raw/gemini_agm.jsonl')})
ASIC = {d['acn']: d for d in pond.read_jsonl_all(NODE, 'width0', 'asic_pub.jsonl', key='acn')}
FIELDS = ['ISIN', 'LEI', 'ACN', 'Share registry', 'Auditor', 'Newswire of habit', 'State', 'Also known as']
STATECOL = {'ISIN': 'ISIN State', 'LEI': 'LEI State', 'ACN': 'ASIC State', 'Share registry': 'Share registry State', 'Auditor': 'Auditor State', 'Newswire of habit': 'Newswire State', 'State': 'State State'}
RBCOL = {'ISIN': 'ISIN read by', 'LEI': 'LEI read by', 'ACN': 'ASIC read by', 'Share registry': 'Share registry read by', 'Auditor': 'Auditor read by', 'Newswire of habit': 'Newswire read by', 'State': 'State read by'}
touched = Counter(); states = Counter(); gaps_new = []; aud_before = Counter(); aud_after = Counter(); reg_before = Counter(); reg_after = Counter()
for ex in TABS:
    if ex not in wb.sheetnames: continue
    ws = wb[ex]; hdr = [c.value for c in ws[1]]; H = {h: i + 1 for i, h in enumerate(hdr)}; base = len(hdr)
    new = ['Auditor source', 'Auditor read by', 'Auditor State', 'Auditor evidence', 'Accounts period end', 'Going concern (annual report)', 'Also known as', 'Alias source', 'Alias read by'] + [f'{f} second source' for f in FIELDS] + [f'{f} second read by' for f in FIELDS] + ['Also known as State', 'State']
    new = [h for h in new if h not in H]
    for i, h in enumerate(new, base + 1):
        c = ws.cell(row=1, column=i, value=h); c.font = BOLD; c.fill = HFILL; c.alignment = Alignment(wrap_text=True, vertical='top')
    col = {h: base + 1 + i for i, h in enumerate(new)}
    def cell(rr, name): return ws.cell(row=rr, column=H[name]) if name in H else ws.cell(row=rr, column=col[name])
    for rr in range(2, ws.max_row + 1):
        k = ex + '|' + str(cell(rr, 'ASX code').value); d = conf.get(k, {}); c = d.get('fields', {}); rp = d.get('report') or {}; tick = k.split('|')[1]
        aud_before[ex] += 1 if cell(rr, 'Auditor').value else 0; reg_before[ex] += 1 if cell(rr, 'Share registry').value else 0
        cl = claude_lei.get(k)
        if cl is not None:
            if cl.get('ruling'):
                if cl['ruling'] != cell(rr, 'LEI').value: cell(rr, 'LEI').value = cl['ruling']; cell(rr, 'LEI source').value = cl.get('source') or f"https://api.gleif.org/api/v1/lei-records/{cl['ruling']}"
                cell(rr, 'LEI read by').value = (cell(rr, 'LEI read by').value or '') + ' · adjudicated by Claude'; cell(rr, 'LEI State').value = 'filled'; touched['Claude:LEI ruled'] += 1
            else:
                cell(rr, 'LEI').value = None; cell(rr, 'LEI State').value = 'conflict'; touched['Claude:LEI blanked'] += 1
                gaps_new.append((ex, tick, 'LEI', f"mapping-file LEI {cl.get('mapped_lei', '')} belongs to another entity ({cl.get('mapped_lei_is', 'unclear')}); adjudicated by Claude, left blank: {(cl.get('reason') or '')[:140]}"))
        ca = claude_acn.get(k)
        if ca is not None and not cell(rr, 'ACN').value:
            if ca.get('ruling'):
                a = ASIC.get(ca['ruling'], {}); cell(rr, 'ACN').value = ca['ruling']; cell(rr, 'ABN').value = a.get('abn', ''); cell(rr, 'ASIC link (unverified — search entry)').value = a.get('src', ca.get('source', ''))
                cell(rr, 'ASIC source').value = ca.get('source', ''); cell(rr, 'ASIC read by').value = 'ASIC bulk register candidates · adjudicated by Claude'; cell(rr, 'ASIC State').value = 'filled'; cell(rr, 'ASIC status').value = a.get('status', ''); touched['Claude:ACN ruled'] += 1
            else:
                touched['Claude:ACN blank with reason'] += 1; gaps_new.append((ex, tick, 'ACN', f"adjudicated by Claude, left blank ({ca.get('why_blank') or 'unclear'}): {(ca.get('reason') or '')[:140]}"))
        if rp:
            if rp.get('auditor') and not cell(rr, 'Auditor').value:
                v = c.get('Auditor', {}).get('value') or rp['auditor']; cell(rr, 'Auditor').value = v; cell(rr, 'Auditor source').value = rp.get('document_url', ''); cell(rr, 'Auditor read by').value = 'read by ChatGPT (batch)'; cell(rr, 'Auditor evidence').value = (rp.get('evidence') or '')[:300]; cell(rr, 'Auditor State').value = c.get('Auditor', {}).get('state') or 'filled'; touched['ChatGPT:Auditor'] += 1
            if rp.get('registry') and not cell(rr, 'Share registry').value:
                cell(rr, 'Share registry').value = c.get('Share registry', {}).get('value') or rp['registry']; cell(rr, 'Share registry source').value = rp.get('document_url', ''); cell(rr, 'Share registry read by').value = 'read by ChatGPT (batch)'; cell(rr, 'Share registry State').value = 'filled'; touched['ChatGPT:Registry'] += 1
            if rp.get('period_end'): cell(rr, 'Accounts period end').value = rp['period_end']; touched['ChatGPT:period end'] += 1
            if rp.get('going_concern'): cell(rr, 'Going concern (annual report)').value = rp['going_concern']; touched['ChatGPT:going concern'] += 1
        g = gem.get(k, {})
        if g.get('registrar') and not cell(rr, 'Share registry').value:
            cell(rr, 'Share registry').value = c.get('Share registry', {}).get('value') or g['registrar']; cell(rr, 'Share registry source').value = g.get('registrar_url', ''); cell(rr, 'Share registry read by').value = 'read by Gemini'; cell(rr, 'Share registry evidence').value = (g.get('registrar_evidence') or '')[:300]; cell(rr, 'Share registry State').value = 'filled'; touched['Gemini:Registry'] += 1
        for f in FIELDS[:-1]:
            ru = rulings.get(k + '#' + f)
            if not ru or f not in c: continue
            if ru.get('ruling'):
                cell(rr, f).value = ru['ruling']; cell(rr, RBCOL[f]).value = (cell(rr, RBCOL[f]).value or '') + ' · adjudicated by Claude'; touched['Claude:conflicts ruled'] += 1
                c[f] = {**c[f], 'state': 'filled', 'read_by2': f"adjudicated by Claude: {ru.get('reason', '')[:120]}"}
            else:
                cell(rr, f).value = None; touched['Claude:conflicts blanked'] += 1
                gaps_new.append((ex, tick, f, f"conflict unresolved, cell blanked — A: {str(ru.get('first', ''))[:60]} vs B: {'; '.join(str(x) for x in ru.get('second', []))[:80]} — adjudicated by Claude: {ru.get('reason', '')[:120]}"))
                c[f] = {**c[f], 'state': 'conflict', 'read_by2': f"adjudicated by Claude: unsettled — {ru.get('reason', '')[:120]}"}
        al = ALIASES.get(k, [])
        if al:
            cell(rr, 'Also known as').value = ' | '.join(a['alias'] for a in al); cell(rr, 'Alias source').value = '\n'.join(a['source'] for a in al); cell(rr, 'Alias read by').value = '\n'.join(a['read_by'] for a in al)
            for a in al: touched['alias:' + a['read_by'].split(' (')[0]] += 1
        summary = Counter()
        for f in FIELDS:
            v = cell(rr, f).value; st = c.get(f, {}).get('state') if v else ''
            scol = STATECOL.get(f, 'Also known as State'); cur = cell(rr, scol).value if f != 'Also known as' else ''
            if v and not st: st = cur or 'sourced'
            if v and cur == 'filled' and st == 'sourced': st = 'filled'
            if st:
                cell(rr, scol).value = st; cell(rr, f'{f} second source').value = '\n'.join(x for x in c.get(f, {}).get('second', []) if x); cell(rr, f'{f} second read by').value = c.get(f, {}).get('read_by2', '')
                summary[st] += 1; states[(f, st)] += 1
            elif not v and f in STATECOL: cell(rr, scol).value = None
        cell(rr, 'State').value = ' · '.join(f'{s} {n}' for s, n in sorted(summary.items())) if summary else ''
        aud_after[ex] += 1 if cell(rr, 'Auditor').value else 0; reg_after[ex] += 1 if cell(rr, 'Share registry').value else 0
    for rr in range(2, ws.max_row + 1):
        for i in range(base + 1, base + 1 + len(new)): ws.cell(row=rr, column=i).font = ARIAL
    for h, i in col.items(): ws.column_dimensions[get_column_letter(i)].width = 30 if 'source' in h or h == 'Also known as' else 18
    ws.auto_filter.ref = f'A1:{get_column_letter(ws.max_column)}{ws.max_row}'
gs = wb['Gaps']
for row in gaps_new: gs.append(list(row) + [1])
def method_rows():
    st = Counter(); [st.__setitem__(s, st[s] + n) for (f, s), n in states.items()]
    ur = json.load(open('raw/chatgpt_reports_usage.json')) if os.path.exists('raw/chatgpt_reports_usage.json') else {}
    pp = jload('raw/perplexity_pages.jsonl'); gl = json.load(open('raw/grok_live_usage.json')) if os.path.exists('raw/grok_live_usage.json') else {}; mc = json.load(open('raw/mistral_count.json')) if os.path.exists('raw/mistral_count.json') else {}
    cf = sum(1 for d in conf.values() for f, v in d.get('fields', {}).items() if v.get('state') in ('confirmed', 'conflict') and 'Tavily' in v.get('read_by2', ''))
    a_src = Counter(a['read_by'].split(' (')[0] for l in ALIASES.values() for a in l); n_rep = len(set(d.get('key') for d in jload('raw/chatgpt_reports.jsonl') if d.get('key')))
    return [('Claude (claude-sonnet-5)', f"Adjudicated from cited evidence: LEI conflicts {len(claude_lei)} ({touched['Claude:LEI ruled']} ruled, {touched['Claude:LEI blanked']} blanked); ACN gaps {len(claude_acn)} ({touched['Claude:ACN ruled']} ruled, {touched['Claude:ACN blank with reason']} blank with reason). Pass 3 conflicts: {len(rulings)} cases, {touched['Claude:conflicts ruled']} ruled, {touched['Claude:conflicts blanked']} blanked. Label 'adjudicated by Claude'."),
            ('ChatGPT (gpt-4.1-mini, Batch API)', f"Read text windows from {ur.get('n', 0)} ASX-lodged documents ({n_rep} issuers: annual reports and Appendix 4E/4D): auditor written {touched['ChatGPT:Auditor']}, share registry {touched['ChatGPT:Registry']}, period end {touched['ChatGPT:period end']}, going-concern flag {touched['ChatGPT:going concern']}. Label 'read by ChatGPT (batch)'."),
            ('Google Gemini (gemini-flash-latest)', f"Long-context read of the 12-month announcement set for {len(gem)} issuers: share registry written {touched['Gemini:Registry']}; AGM / record-date findings on the Disclosure workbook. Label 'read by Gemini'."),
            ('Perplexity (Agent API, preset low)', f"Located company pages for issuers with no events or no website: {sum(1 for d in pp if d.get('verified'))} verified of {len(pp)} asked; {sum(1 for d in pp if d.get('alias'))} aliases. Label 'read by Perplexity (agent · low)'. Sonar Chat Completions retire 2026-09-27; this rail never used them."),
            ('Grok (grok-4.6)', f"Live layer in the weekly refresh; validation run found {gl.get('halts', 0)} halt/suspension/reinstatement items and {gl.get('newswire', 0)} silent-issuer items. Label 'read by Grok (live)'."),
            ('Mistral (mistral-small-latest)', f"Non-English announcements found: {mc.get('n_targets', 0)}; read {mc.get('n_targets', 0)}."),
            ('Tavily (search)', f"Second-source reads for Pass 3: {cf} fields resolved to confirmed or conflict; alias rematch on the Disclosure workbook."),
            ('Cloudflare', 'Touched nothing on the issuer record.'),
            ('Sources (not engines)', 'Aliases: ' + ', '.join(f'{k} {n}' for k, n in a_src.most_common()) + '. States across the eight fields: ' + ', '.join(f'{s} {n}' for s, n in sorted(st.items())) + '.'),
            ('Auditor / registry fill', 'Auditor before: ' + ', '.join(f'{ex} {aud_before[ex]}' for ex in TABS if ex in wb.sheetnames) + '; after: ' + ', '.join(f'{ex} {aud_after[ex]}' for ex in TABS if ex in wb.sheetnames) + '. Share registry before: ' + ', '.join(f'{ex} {reg_before[ex]}' for ex in TABS if ex in wb.sheetnames) + '; after: ' + ', '.join(f'{ex} {reg_after[ex]}' for ex in TABS if ex in wb.sheetnames) + '.'),
            ('Rule', 'Aliases sourced only (ASIC former names, the ASX display name, GLEIF other names, wire page names); never a guess. States: sourced = one source read; filled = written by adjudication or a lab read; confirmed = two independent sources agree, both cited; conflict = the second source disagrees, sent to Claude or left blank with reason.')]
if 'Method' in wb.sheetnames:
    mt = wb['Method']; mt.append([]); mt.append(['Passes 2 and 3 (ORDER-012, ' + TODAY.isoformat() + ')', 'Engine duty and count of fields touched on Australia'])
    for c in mt[mt.max_row]: c.font = BOLD
    for a, b in method_rows():
        mt.append([a, b])
        for c in mt[mt.max_row]: c.font = ARIAL; c.alignment = Alignment(wrap_text=True, vertical='top')
for ws_ in wb.worksheets:
    for row_ in ws_.iter_rows():
        for c_ in row_:
            if isinstance(c_.value, str) and CTRL0.search(c_.value): c_.value = CTRL0.sub('', c_.value)
wb.save(SRC); _ad = pond.assembled(NODE); shutil.copy(SRC, os.path.join(_ad, 'au-issuers.xlsx'))
print('saved', SRC, '| versioned copy', _ad); print('touched', dict(touched)); print('states', sorted(states.items())); print('auditor before', dict(aud_before), 'after', dict(aud_after)); print('registry before', dict(reg_before), 'after', dict(reg_after))
