r"""Rebuilds jp-issuers.xlsx with the Fill pass applied (ORDER-017 re-cut), into a NEW assembled drop beside the Width 0 workbook (mirror refreshed):
  Auditor / Share registrar / Accounts period end / Going concern ... from Gemini's Japanese read of the 有価証券報告書 text windows (State filled;
                                                                     source = the EDINET document page; read-by = the Gemini label)
  Annual report ......................................................... the EDINET document page of the report read (docTypeCode 120)
  Also known as ......................................................... issuer page <title> found by Perplexity (agent · fast), sourced
Mistral's review never writes a cell: a value Mistral DISPUTED is left as filled with ' · disputed on review' in the read-by and a Gaps note; its
flags live on the Review tab of the Disclosure workbook. Prints touched counters and State counts."""
from fc_common import *
import shutil
from collections import Counter
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
X = ISSUERS_XLSX
gem = {d['key']: d for d in jload('raw/gemini_reads.jsonl') if d.get('docID')}
docs = {d['key']: d for d in jload('raw/edinet_docs.jsonl') if d.get('docID')}
xb = {d['key']: d for d in jload('raw/edinet_xbrl.jsonl') if d.get('docID')}
pp = {d['key']: d for d in jload('raw/perplexity_pages.jsonl')}
mis = {}
for d in jload('raw/mistral_reads.jsonl'):
    if d.get('kind') == 'gemini_doc': mis[d['key']] = d
wb = load_workbook(X); ARIAL = Font(name='Arial', size=10); touched = Counter(); states = Counter(); gaps_new = []
NEWCOLS = ['Accounts period end', 'Going concern (annual report)', 'Also known as', 'Alias source', 'Alias read by']
aud_before = {}; aud_after = {}; reg_before = {}; reg_after = {}
for ex in TABS:
    if ex not in wb.sheetnames: continue
    ws = wb[ex]; hdr = [c.value for c in ws[1]]; H = {h: i + 1 for i, h in enumerate(hdr)}
    gi = H['Gaps']
    for c in NEWCOLS:
        if c not in H:
            ws.insert_cols(gi); ws.cell(row=1, column=gi).value = c; ws.cell(row=1, column=gi).font = Font(name='Arial', size=10, bold=True)
            hdr = [c2.value for c2 in ws[1]]; H = {h: i + 1 for i, h in enumerate(hdr)}; gi = H['Gaps']
    def cell(rr, name): return ws.cell(row=rr, column=H[name])
    aud_before[ex] = sum(1 for rr in range(2, ws.max_row + 1) if cell(rr, 'Auditor').value); reg_before[ex] = sum(1 for rr in range(2, ws.max_row + 1) if cell(rr, 'Share registrar').value)
    for rr in range(2, ws.max_row + 1):
        sym = cell(rr, 'Symbol').value
        if sym is None: continue
        k = ex + '|' + str(sym); g = gem.get(k); d = docs.get(k); m = mis.get(k) or {}; ck = m.get('checks') or {}; extra_gaps = []
        if d:
            cell(rr, 'Annual report').value = d['document_url']; cell(rr, 'Annual report source').value = d['document_url']; cell(rr, 'Annual report read by').value = f"EDINET API v2 documents list (有価証券報告書, docTypeCode 120, filed {d.get('doc_date')})"; touched['EDINET:annual report link'] += 1
        x = xb.get(k)
        if x and x.get('auditor'):
            cell(rr, 'Auditor').value = x['auditor']; cell(rr, 'Auditor source').value = x['document_url']; cell(rr, 'Auditor read by').value = x['read_by'] + f" — element {x.get('auditor_element')}"; cell(rr, 'Auditor State').value = 'sourced'; touched['EDINET XBRL:Auditor'] += 1
            if len(x.get('audit_firms') or []) > 1: cell(rr, 'Gaps').value = ((cell(rr, 'Gaps').value or '') + '; ' if cell(rr, 'Gaps').value else '') + 'Auditor: joint audit — ' + ' / '.join(f['name'] for f in x['audit_firms'])
        if x and x.get('fiscal_year_end'): cell(rr, 'Accounts period end').value = x['fiscal_year_end']; touched['EDINET XBRL:period end'] += 1
        if x and x.get('going_concern_windows'): cell(rr, 'Going concern (annual report)').value = 'going-concern note present (継続企業の前提; XBRL text block ' + ', '.join(x.get('going_concern_elements') or [])[:120] + ')'; touched['EDINET XBRL:going concern block'] += 1
        if g and not g.get('error'):
            def put(field, val, ok_key, statecol, rbcol, srccol):
                if not val: return
                if cell(rr, field).value and str(cell(rr, field).value).strip() == val: cell(rr, statecol).value = 'confirmed'; touched[f'Gemini:{field} agrees'] += 1; return
                cell(rr, field).value = val; cell(rr, srccol).value = g['document_url']; rb = g['read_by']
                if ck.get(ok_key) is False: rb += ' · disputed on review by Mistral (ja)'; extra_gaps.append(f"{field}: Mistral review disputes the Gemini reading ({(m.get('reason') or '')[:120]})"); touched[f'Mistral:{field} disputed'] += 1
                cell(rr, rbcol).value = rb; cell(rr, statecol).value = 'filled'; touched[f'Gemini:{field}'] += 1
            if not (x and x.get('auditor')): put('Auditor', g.get('auditor'), 'auditor_ok', 'Auditor State', 'Auditor read by', 'Auditor source')
            put('Share registrar', g.get('registrar'), 'registrar_ok', 'Share registrar State', 'Share registrar read by', 'Share registrar source')
            if g.get('registrar_evidence') and cell(rr, 'Share registrar').value == g.get('registrar'): cell(rr, 'Share registrar evidence').value = g['registrar_evidence'][:300]
            if g.get('period_end') and not (x and x.get('fiscal_year_end')): cell(rr, 'Accounts period end').value = g['period_end']; touched['Gemini:period end'] += 1
            if g.get('going_concern') and not (x and x.get('going_concern_windows')): cell(rr, 'Going concern (annual report)').value = {'stated': 'material events stated (継続企業の前提に関する重要事象)', 'not_stated': 'none stated', 'unclear': 'unclear'}.get(g['going_concern'], g['going_concern']); touched['Gemini:going concern'] += 1
        p = pp.get(k)
        if p and p.get('alias'):
            cell(rr, 'Also known as').value = p['alias']; cell(rr, 'Alias source').value = p.get('url', ''); cell(rr, 'Alias read by').value = p.get('alias_read_by', ''); touched['alias:issuer page <title>'] += 1
        if extra_gaps: cell(rr, 'Gaps').value = ((cell(rr, 'Gaps').value or '') + '; ' if cell(rr, 'Gaps').value else '') + '; '.join(extra_gaps)
        for f, sc in (('Auditor', 'Auditor State'), ('Share registrar', 'Share registrar State'), ('ISIN', 'ISIN State'), ('LEI', 'LEI State'), ('Also known as', None)):
            if cell(rr, f).value: states[(f, cell(rr, sc).value if sc else 'sourced')] += 1
        for c2 in ws[rr]: c2.font = ARIAL
    aud_after[ex] = sum(1 for rr in range(2, ws.max_row + 1) if cell(rr, 'Auditor').value); reg_after[ex] = sum(1 for rr in range(2, ws.max_row + 1) if cell(rr, 'Share registrar').value)
# Method tab lines
mt = wb['Method']; BOLD = Font(name='Arial', size=10, bold=True)
mt.append([]); mt.append(['Fill pass (ORDER-017 re-cut, ' + TODAY.isoformat() + ')', 'Engine duty and count on the Japan issuers workbook'])
for c in mt[mt.max_row]: c.font = BOLD
mc = json.load(open('raw/mistral_count.json')) if os.path.exists('raw/mistral_count.json') else {}
for a, b in [('EDINET (API v2)', f"Latest 有価証券報告書 per issuer: XBRL-to-CSV facts for {len(xb)} reports (audit firm as the tagged fact jpcrp_cor:AuditFirm1…, fiscal year end from jpdei, going-concern text blocks) written as sourced ({touched['EDINET XBRL:Auditor']} auditors, {touched['EDINET XBRL:period end']} period ends); the PDF reduced to Japanese text windows for {len(docs)} reports; the document page is the annual report link and the source of every filled field."),
             ('Google Gemini (gemini-flash-latest)', f"Primary reader of the Japanese windows: auditor written {touched['Gemini:Auditor']} (agrees with an existing value {touched['Gemini:Auditor agrees']}), share-register administrator written {touched['Gemini:Share registrar']}, period end {touched['Gemini:period end']}, going-concern statement {touched['Gemini:going concern']}. Label 'read by Gemini (ja)'. Values verbatim in Japanese; no translation."),
             ('Perplexity (Agent API, preset fast)', f"Search layer: company pages located for {sum(1 for d in pp.values() if d.get('verified'))} issuers (verified by fetch); page titles became sourced aliases ({touched['alias:issuer page <title>']})."),
             ('Grok (grok-4.6)', 'Second engine: live layer (halts, silent issuers) on the Disclosure workbook.'),
             ('Mistral (mistral-small-latest)', f"Review only: {mc.get('reviewed', 0)} items re-read in Japanese — {mc.get('confirmed', 0)} confirmed, {mc.get('disputed', 0)} disputed ({touched['Mistral:Auditor disputed'] + touched['Mistral:Share registrar disputed']} field readings marked disputed on this workbook), {mc.get('flags', 0)} Mistral-only findings on the Review tab of the Disclosure workbook. No field written."),
             ('State', 'sourced = one source; filled = lab-derived value with the document as source; confirmed = the Gemini reading agrees with a value already sourced.')]:
    mt.append([a, b])
    for c in mt[mt.max_row]: c.font = ARIAL; c.alignment = Alignment(wrap_text=True, vertical='top')
_ad = pond.assembled(NODE); out = os.path.join(_ad, 'jp-issuers.xlsx'); wb.save(out); shutil.copy(out, r'C:\ALLOOLOO\CM-KG\ISSUERS\jp-issuers.xlsx')
print('saved', out, '| mirror refreshed')
print('touched', dict(touched)); print('states', sorted(states.items()))
print('auditor before', aud_before, 'after', aud_after); print('registry before', reg_before, 'after', reg_after)
