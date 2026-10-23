"""Pass 2.1 — the annual report (deterministic, from the filing). For every roster line, the newest English annual report Width 1 found on HKEXnews
(HKEX headline category 'Financial Statements/ESG Information - [Annual Report]') is the Annual report field (sourced, HKEXnews). Its text is read once
by Tavily page extraction and the Corporate Information page is searched for the auditor and the Hong Kong (branch) share registrar as the issuer
filed them. A value found here is read from the filing itself: state sourced, read by 'annual report <date> (HKEXnews), Corporate Information'.
Raw: raw/annual_reports.jsonl; the text window around Corporate Information kept in raw/reports/<code>.txt."""
import re
from fc_common import *
EV = events(); latest = {}
for e in EV:
    if e.get('event_type') == 'annual_report' and str(e.get('url', '')).lower().endswith('.pdf'):
        k = e['exchange'] + '|' + e['ticker']
        if k not in latest or e['date'] > latest[k]['date']: latest[k] = e
AUD = re.compile(r"(?is)\b(?:independent\s+)?auditors?\b[\s:]*\n?\s*((?:[A-Z][\w&.,'’()\- ]{2,90}?)(?:Certified Public Accountants|Public Interest Entity Auditor|CPA Limited|CPA Co\.?,? Limited|\(Hong Kong\)|Limited|LLP|& Co\.?))")
REG = re.compile(r"(?is)\b(?:(?:hong\s+kong|branch|principal)\s+)*(?:share\s+)?registrars?(?:\s+and\s+transfer\s+(?:office|agent))?(?:\s+in\s+hong\s+kong)?\b[\s:]*\n?\s*([A-Z][\w&.,'’()\- ]{3,90}?(?:Limited|Ltd\.?|Pty Limited))")
def window(t):
    # the Corporate Information page sits before or after the contents and the share registrar often in Shareholder Information at the back:
    # every passage that names a registrar or an auditor (the auditor's own report heading aside) is kept, in reading order
    spans = [(max(0, m.start() - 40), m.end() + 260) for m in re.finditer(r"(?i)share\s+registrar|\bregistrars?\b|\bauditors?\b(?!['’]s\s+report)", t[:600000])]
    return '\n'.join(t[a:b] for a, b in spans[:60]) or t[:20000]
# closed lists (the names as the firms write them in Hong Kong filings); a passage naming one of these is read as that firm, written as the passage spells it
AUDIT_FIRMS = ['PricewaterhouseCoopers', 'KPMG', 'Deloitte Touche Tohmatsu', 'Ernst & Young', 'BDO Limited', 'Grant Thornton Hong Kong Limited', 'RSM Hong Kong', 'Forvis Mazars CPA Limited', 'Mazars CPA Limited',
               'Moore CPA Limited', 'Moore Stephens CPA Limited', 'Crowe (HK) CPA Limited', 'HLB Hodgson Impey Cheng Limited', 'ZHONGHUI ANDA CPA Limited', 'SHINEWING (HK) CPA Limited', 'Baker Tilly Hong Kong Limited',
               'Prism Hong Kong Limited', 'Prism Hong Kong and Shanghai Limited', 'McMillan Woods (Hong Kong) CPA Limited', 'Elite Partners CPA Limited', 'CL Partners CPA Limited', 'Confucius International CPA Limited',
               'Linksfield CPA Limited', 'PKF Hong Kong Limited', 'Ascenda Cachet CPA Limited', 'Asian Alliance (HK) CPA Limited', 'Zenith CPA Limited', 'Infinity CPA Limited', 'Yongtuo Fuson CPA Limited', 'Union Alpha CPA Limited',
               'AOGB CPA Limited', 'Mazars', 'Forvis Mazars', 'Crowe', 'Baker Tilly', 'Grant Thornton', 'BDO']
HK_REGISTRARS = ['Computershare Hong Kong Investor Services Limited', 'Tricor Investor Services Limited', 'Boardroom Share Registrars (HK) Limited', 'Union Registrars Limited', 'Hong Kong Registrars Limited',
                 'Link Market Services (Hong Kong) Pty Limited', 'Tricor Standard Limited', 'Tricor Tengis Limited', 'Tricor Secretaries Limited', 'Tricor Abacus Limited', 'Hong Kong Registrars', 'Computershare Hong Kong']
def known(names, t):
    best = None
    for n in names:
        m = re.search(re.escape(n), t, re.I)
        if m and (best is None or m.start() < best[0] or (m.start() == best[0] and len(n) > len(best[1]))): best = (m.start(), t[m.start():m.end()])
    return best[1] if best else None
def pick(rx, t, names):
    k = known(names, t)
    if k: return re.sub(r'\s+', ' ', k).strip()
    for m in rx.finditer(t):
        v = re.sub(r'\s+', ' ', m.group(1)).strip(' ,.:;')
        v = re.sub(r'^(?:.*?\b(?:audited\s+by|by|is|of\s+the\s+company,?)\s+)', '', v, flags=re.I).strip(' ,.:;')
        if 4 <= len(v) <= 120 and not CJK.search(v) and v[0].isupper(): return v
    return None
def read(r):
    k = key_of(r); e = latest.get(k)
    if not e: return {'annual_report': None, 'why': 'no English annual report in the Width 1 window'}
    res = tavily_extract([e['url']])
    rr = (res.get('results') or [{}])[0] if res.get('results') else {}
    txt = rr.get('raw_content') or ''
    out = {'annual_report': e['url'], 'annual_report_date': e['date'], 'annual_report_title': e['title'], 'extract_chars': len(txt), 'extract_error': res.get('error') or ((res.get('failed_results') or [{}])[0].get('error') if res.get('failed_results') else None)}
    if txt:
        w = window(txt); open(f"raw/reports/{r['Stock code']}.txt", 'w', encoding='utf-8').write(w)
        out['auditor'] = pick(AUD, w, AUDIT_FIRMS); out['registrar'] = pick(REG, w, HK_REGISTRARS)
    return out
if __name__ == '__main__':
    rows = all_rows(); print('roster', len(rows), 'with an English annual report in the window', sum(1 for r in rows if key_of(r) in latest), flush=True)
    resume('annual_reports', read, rows, threads=int(E.get('THREADS', '8')))
    # second pass (2026-10-22): lines the first pass found no annual report for, after the combined-heading fix in the Width 1 assembler
    first = {d['key']: d for d in jload('raw/annual_reports.jsonl')}
    again = [r for r in rows if key_of(r) in latest and not (first.get(key_of(r)) or {}).get('annual_report')]
    print('second pass targets', len(again), flush=True); resume('annual_reports2', read, again, threads=int(E.get('THREADS', '8')))
