r"""Rebuilds CM-KG\ISSUERS\uk-issuers.xlsx with passes 2 and 3 applied: 'Also known as' (+ source, read by); Claude rulings written into LEI /
Companies House number / Auditor where the cell was blank or in conflict (read by 'adjudicated by Claude'); ChatGPT accounts reads written into
Auditor / Registrar where blank (read by 'read by ChatGPT (batch)'), plus 'Accounts period end' and 'Going concern (accounts)'; Gemini registrar
reads where blank (read by 'read by Gemini'); per-field State columns updated (sourced / filled / confirmed / conflict) with second source and
second read-by; a summary State column; Method tab listing all eight engines with the exact duty and count on the UK. The Width 0 workbook
is kept beside it as uk-issuers-width0.xlsx."""
import shutil
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from fc_common import *
from collections import Counter
SRC = ISSUERS_XLSX; BAK = SRC.replace('uk-issuers.xlsx', 'uk-issuers-width0.xlsx')
if not os.path.exists(BAK): shutil.copy(SRC, BAK)
wb = load_workbook(BAK)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
conf = {d['key']: d for d in jload('raw/confirm_fields.jsonl')}
ALIASES = all_aliases()
claude_lei = {d['key']: d for d in jload('raw/claude_lei.jsonl')}; claude_ch = {d['key']: d for d in jload('raw/claude_ch.jsonl')}; claude_aud = {d['key']: d for d in jload('raw/claude_auditor.jsonl')}
rulings = {d['key']: d for d in jload('raw/conflict_rulings.jsonl')}
gem = {d['key']: d for d in jload('raw/gemini_agm.jsonl')}
CTRL0 = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
def _clean(o):  # evidence and reason strings read from page text / PDFs can carry control characters openpyxl refuses on assignment
    if isinstance(o, str): return CTRL0.sub('', o)
    if isinstance(o, dict): return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, list): return [_clean(v) for v in o]
    return o
conf = _clean(conf); ALIASES = _clean(ALIASES); claude_lei = _clean(claude_lei); claude_ch = _clean(claude_ch); claude_aud = _clean(claude_aud); rulings = _clean(rulings); gem = _clean(gem)
FIELDS = ['ISIN', 'LEI', 'Companies House number', 'Registrar', 'Auditor', 'Newswire of habit', 'Incorporation jurisdiction', 'Also known as']
STATECOL = {'ISIN': 'ISIN State', 'LEI': 'LEI State', 'Companies House number': 'Companies House State', 'Registrar': 'Registrar State', 'Auditor': 'Auditor State', 'Newswire of habit': 'Newswire State', 'Incorporation jurisdiction': 'Jurisdiction State'}
SRCCOL = {'ISIN': 'ISIN source', 'LEI': 'LEI source', 'Companies House number': 'Companies House source', 'Registrar': 'Registrar source', 'Auditor': 'Auditor source', 'Newswire of habit': 'Newswire releases seen', 'Incorporation jurisdiction': 'Jurisdiction source'}
RBCOL = {'ISIN': 'ISIN read by', 'LEI': 'LEI read by', 'Companies House number': 'Companies House read by', 'Registrar': 'Registrar read by', 'Auditor': 'Auditor read by', 'Newswire of habit': 'Newswire read by', 'Incorporation jurisdiction': 'Jurisdiction read by'}
touched = Counter(); states = Counter(); gaps_new = []; aud_before = Counter(); aud_after = Counter()
for ex in TABS:
    ws = wb[ex]; hdr = [c.value for c in ws[1]]; H = {h: i + 1 for i, h in enumerate(hdr)}; base = len(hdr)
    new = ['Also known as', 'Alias source', 'Alias read by', 'Accounts period end', 'Going concern (accounts)', 'Accounts read by'] + [f'{f} second source' for f in FIELDS] + [f'{f} second read by' for f in FIELDS] + ['Also known as State', 'State']
    for i, h in enumerate(new, base + 1):
        c = ws.cell(row=1, column=i, value=h); c.font = BOLD; c.fill = HFILL; c.alignment = Alignment(wrap_text=True, vertical='top')
    col = {h: base + 1 + i for i, h in enumerate(new)}
    def cell(rr, name): return ws.cell(row=rr, column=H[name]) if name in H else ws.cell(row=rr, column=col[name])
    for rr in range(2, ws.max_row + 1):
        k = ex + '|' + str(cell(rr, 'Ticker (TIDM)').value); d = conf.get(k, {}); c = d.get('fields', {}); ar = d.get('accounts') or {}; tick = k.split('|')[1]
        aud_before[ex] += 1 if cell(rr, 'Auditor').value else 0
        # Claude: LEI conflicts
        cl = claude_lei.get(k)
        if cl is not None:
            if cl.get('ruling'):
                if cl['ruling'] != cell(rr, 'LEI').value: cell(rr, 'LEI').value = cl['ruling']; cell(rr, 'LEI source').value = cl.get('source') or f"https://api.gleif.org/api/v1/lei-records/{cl['ruling']}"
                cell(rr, 'LEI read by').value = (cell(rr, 'LEI read by').value or '') + ' · adjudicated by Claude'; cell(rr, 'LEI State').value = 'filled'; touched['Claude:LEI ruled'] += 1
            else:
                cell(rr, 'LEI').value = None; cell(rr, 'LEI State').value = 'conflict'; touched['Claude:LEI blanked'] += 1
                gaps_new.append((ex, tick, 'LEI', f"mapping-file LEI {cl.get('mapped_lei', '')} belongs to another entity ({cl.get('mapped_lei_is', 'unclear')}); adjudicated by Claude, left blank: {(cl.get('reason') or '')[:140]}"))
        # Claude: Companies House number
        cc = claude_ch.get(k)
        if cc is not None and not cell(rr, 'Companies House number').value:
            if cc.get('ruling'):
                n = cc['ruling']; cell(rr, 'Companies House number').value = n; cell(rr, 'Companies House profile link').value = f'https://find-and-update.company-information.service.gov.uk/company/{n}'
                cell(rr, 'Companies House source').value = cc.get('source', ''); cell(rr, 'Companies House read by').value = 'Companies House API name search · adjudicated by Claude'; cell(rr, 'Companies House State').value = 'filled'; touched['Claude:CH number ruled'] += 1
                cell(rr, 'Accounts filing (Companies House)').value = f'https://find-and-update.company-information.service.gov.uk/company/{n}/filing-history?category=accounts'
            else:
                touched['Claude:CH blank with reason'] += 1
                gaps_new.append((ex, tick, 'Companies House number', f"adjudicated by Claude, left blank ({cc.get('why_blank') or 'unclear'}): {(cc.get('reason') or '')[:140]}"))
        # Claude: auditor strings
        ca = claude_aud.get(k)
        if ca is not None and not cell(rr, 'Auditor').value:
            if ca.get('ruling'): cell(rr, 'Auditor').value = ca['ruling']; cell(rr, 'Auditor source').value = ca.get('source') or ''; cell(rr, 'Auditor read by').value = 'adjudicated by Claude'; cell(rr, 'Auditor State').value = 'filled'; touched['Claude:Auditor ruled'] += 1
            else: gaps_new.append((ex, tick, 'Auditor', 'adjudicated by Claude: left blank — ' + (ca.get('reason') or '')[:160]))
        # ChatGPT accounts read
        if ar:
            if ar.get('auditor') and not cell(rr, 'Auditor').value:
                cell(rr, 'Auditor').value = c.get('Auditor', {}).get('value') or ar['auditor']; cell(rr, 'Auditor source').value = ar.get('document_url', ''); cell(rr, 'Auditor read by').value = 'read by ChatGPT (batch)'; cell(rr, 'Auditor evidence').value = (ar.get('evidence') or '')[:300]; cell(rr, 'Auditor State').value = 'filled'; touched['ChatGPT:Auditor'] += 1
            if ar.get('registrar') and not cell(rr, 'Registrar').value:
                cell(rr, 'Registrar').value = c.get('Registrar', {}).get('value') or ar['registrar']; cell(rr, 'Registrar source').value = ar.get('document_url', ''); cell(rr, 'Registrar read by').value = 'read by ChatGPT (batch)'; cell(rr, 'Registrar State').value = 'filled'; touched['ChatGPT:Registrar'] += 1
            if ar.get('period_end'): cell(rr, 'Accounts period end').value = ar['period_end']; touched['ChatGPT:period end'] += 1
            if ar.get('going_concern'): cell(rr, 'Going concern (accounts)').value = ar['going_concern']; touched['ChatGPT:going concern'] += 1
            cell(rr, 'Accounts read by').value = 'read by ChatGPT (batch) — ' + (ar.get('document_url') or '')
        # Gemini registrar
        g = gem.get(k, {})
        if g.get('registrar') and not cell(rr, 'Registrar').value:
            cell(rr, 'Registrar').value = c.get('Registrar', {}).get('value') or g['registrar']; cell(rr, 'Registrar source').value = g.get('registrar_url', ''); cell(rr, 'Registrar read by').value = 'read by Gemini'; cell(rr, 'Registrar evidence').value = (g.get('registrar_evidence') or '')[:300]; cell(rr, 'Registrar State').value = 'filled'; touched['Gemini:Registrar'] += 1
        # Newswire filled from the Width 1 event set
        if c.get('Newswire of habit', {}).get('state') == 'filled' and not cell(rr, 'Newswire of habit').value:
            cell(rr, 'Newswire of habit').value = c['Newswire of habit']['value']; cell(rr, 'Newswire read by').value = 'Width 1 12-month event set (majority wire)'; cell(rr, 'Newswire State').value = 'filled'; touched['Width 1 events:Newswire'] += 1
        # Pass 3 conflict rulings
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
        # aliases
        al = ALIASES.get(k, [])
        if al:
            cell(rr, 'Also known as').value = ' | '.join(a['alias'] for a in al); cell(rr, 'Alias source').value = '\n'.join(a['source'] for a in al); cell(rr, 'Alias read by').value = '\n'.join(a['read_by'] for a in al)
            for a in al: touched['alias:' + a['read_by'].split(' (')[0]] += 1
        # states
        summary = Counter()
        for f in FIELDS:
            v = cell(rr, f).value
            st = c.get(f, {}).get('state') if v else ''
            scol = STATECOL.get(f, 'Also known as State')
            cur = cell(rr, scol).value if f != 'Also known as' else ''
            if v and not st: st = cur or 'sourced'
            if v and cur == 'filled' and st == 'sourced': st = 'filled'
            if v and cur in ('filled',) and st == 'confirmed': st = 'confirmed'
            if st:
                cell(rr, scol).value = st; cell(rr, f'{f} second source').value = '\n'.join(x for x in c.get(f, {}).get('second', []) if x); cell(rr, f'{f} second read by').value = c.get(f, {}).get('read_by2', '')
                summary[st] += 1; states[(f, st)] += 1
            elif not v and f in STATECOL: cell(rr, scol).value = None
        cell(rr, 'State').value = ' · '.join(f'{s} {n}' for s, n in sorted(summary.items())) if summary else ''
        aud_after[ex] += 1 if cell(rr, 'Auditor').value else 0
    for rr in range(2, ws.max_row + 1):
        for i in range(base + 1, base + 1 + len(new)): ws.cell(row=rr, column=i).font = ARIAL
    for h, i in col.items(): ws.column_dimensions[get_column_letter(i)].width = 30 if 'source' in h or h == 'Also known as' else 18
    ws.auto_filter.ref = f'A1:{get_column_letter(ws.max_column)}{ws.max_row}'
gs = wb['Gaps']
for row in gaps_new: gs.append(list(row) + [1])
for r_ in gs.iter_rows(min_row=max(2, gs.max_row - len(gaps_new)), max_row=gs.max_row):
    for c_ in r_: c_.font = ARIAL
def method_rows():
    st = Counter(); [st.__setitem__(s, st[s] + n) for (f, s), n in states.items()]
    ua = json.load(open('raw/chatgpt_accounts_usage.json')) if os.path.exists('raw/chatgpt_accounts_usage.json') else {}; ur = json.load(open('raw/chatgpt_results_usage.json')) if os.path.exists('raw/chatgpt_results_usage.json') else {}
    pp = jload('raw/perplexity_pages.jsonl'); gl = json.load(open('raw/grok_live_usage.json')) if os.path.exists('raw/grok_live_usage.json') else {}
    mc = json.load(open('raw/mistral_count.json')) if os.path.exists('raw/mistral_count.json') else {}
    cf = sum(1 for d in conf.values() for f, v in d.get('fields', {}).items() if v.get('state') in ('confirmed', 'conflict') and 'Tavily' in v.get('read_by2', ''))
    a_src = Counter(a['read_by'].split(' (')[0] for l in ALIASES.values() for a in l)
    return [
        ('Claude (claude-sonnet-5)', f"Adjudicated from cited evidence: LEI conflicts {len(claude_lei)} ({touched['Claude:LEI ruled']} ruled, {touched['Claude:LEI blanked']} left blank); unmatched Companies House rows {len(claude_ch)} ({touched['Claude:CH number ruled']} numbers written, {touched['Claude:CH blank with reason']} blank with reason); auditor strings {len(claude_aud)} ({touched['Claude:Auditor ruled']} ruled). Pass 3 conflicts: {len(rulings)} cases, {touched['Claude:conflicts ruled']} ruled, {touched['Claude:conflicts blanked']} unsettled and blanked. Rematch collisions on the Disclosure workbook (see its Method tab). Label 'adjudicated by Claude'."),
        ('ChatGPT (gpt-4.1-mini, Batch API)', f"Read {ua.get('n', 0)} accounts-PDF parts ({len(set(k for k, d in conf.items() if (d.get('accounts') or {}).get('number')))} issuers' latest Companies House accounts, page images) and {ur.get('n', 0)} results announcements. Written here: auditor {touched['ChatGPT:Auditor']}, registrar {touched['ChatGPT:Registrar']}, accounts period end {touched['ChatGPT:period end']}, going-concern flag {touched['ChatGPT:going concern']}; auditor confirmations/conflicts via the second-source check. Label 'read by ChatGPT (batch)'."),
        ('Google Gemini (gemini-flash-latest)', f"Long-context read of the 12-month RNS set for {len(gem)} issuers (no AGM event or no registrar): registrar written {touched['Gemini:Registrar']}; AGM / record-date findings on the Disclosure workbook. Label 'read by Gemini'."),
        ('Perplexity', f"Located the current regulatory-news page for issuers whose Investegate page was missing or empty: {sum(1 for d in pp if d.get('verified'))} verified of {len(pp)} asked; {sum(1 for d in pp if d.get('alias'))} aliases from those pages' own titles. This run used sonar-pro (grounded chat completions), label 'read by Perplexity (agent)'. From ORDER-010 Part B the worker calls the Agent API (POST /v1/responses, preset 'low' for grounded page recovery, 'fast' for cold single-fact reads; sources from the search_results output item), label 'read by Perplexity (agent · low/fast)'. Sonar Chat Completions retire on 2026-09-27; the UK weekly refresh runs on the Agent API from its first run."),
        ('Grok (grok-4.6, Responses API + web/X search)', f"Live layer in the weekly refresh (suspensions, restorations, cancellations; silent-issuer news): validation run on the backfill day found {gl.get('halts', 0)} suspension/restoration items and {gl.get('newswire', 0)} silent-issuer items with URLs; nothing written to this workbook. Label 'read by Grok (live)'."),
        ('Mistral (mistral-small-latest)', f"Non-English announcements in the UK 12-month set: {mc.get('n_targets', 0)} found, {mc.get('n_targets', 0)} read. Nothing written to this workbook."),
        ('Tavily (search)', f"Second-source reads for Pass 3 (ISIN, registrar, auditor): {cf} fields resolved to confirmed or conflict from a second page on a different domain; alias rematch searches on the Disclosure workbook."),
        ('Cloudflare', 'Touched nothing on the issuer record (network and doors only).'),
        ('Sources (not engines)', 'Aliases: ' + ', '.join(f'{k} {n}' for k, n in a_src.most_common()) + '. States across the eight fields: ' + ', '.join(f'{s} {n}' for s, n in sorted(st.items())) + '.'),
        ('Auditor fill', 'Before passes 2–3: ' + ', '.join(f'{ex} {aud_before[ex]}' for ex in TABS) + '. After: ' + ', '.join(f'{ex} {aud_after[ex]}' for ex in TABS) + '.'),
        ('Rule', 'Aliases sourced only (Companies House previous names, GLEIF other names, the issuer\'s own news page, the exchange profile); never a guess. States: sourced = one source read; filled = written by adjudication or a lab read; confirmed = two independent sources agree, both cited; conflict = the second source disagrees, sent to Claude or left blank with reason.'),
    ]
if 'Method' in wb.sheetnames:
    mt = wb['Method']; mt.append([]); mt.append(['Passes 2 and 3 (ORDER-009, ' + TODAY.isoformat() + ')', 'Engine duty and count of fields touched on the United Kingdom'])
    for c in mt[mt.max_row]: c.font = BOLD
    for a, b in method_rows():
        mt.append([a, b])
        for c in mt[mt.max_row]: c.font = ARIAL; c.alignment = Alignment(wrap_text=True, vertical='top')
CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')  # evidence snippets from page text can carry control characters openpyxl refuses
for ws_ in wb.worksheets:
    for row_ in ws_.iter_rows():
        for c_ in row_:
            if isinstance(c_.value, str) and CTRL.search(c_.value): c_.value = CTRL.sub('', c_.value)
wb.save(SRC)
import pond; _ad = pond.assembled('uk-cm-kg'); shutil.copy(SRC, os.path.join(_ad, 'uk-issuers.xlsx'))  # pond rule 2: versioned output
print('saved', SRC, '| versioned copy', _ad); print('touched', dict(touched)); print('states', sorted(states.items())); print('auditor before', dict(aud_before), 'after', dict(aud_after))
