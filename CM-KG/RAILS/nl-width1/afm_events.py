"""AFM notification registers (afm.nl, public register pages) — the regulator's trail per Dutch issuer, read by issuer keyword on each register page:
inside information (openbaarmaking-voorwetenschap = ad hoc), financial reporting (financiele-verslaggeving = results), directors' and supervisory board
transactions (bestuurders-commissarissen), substantial holdings (substantiele-deelnemingen-en-bruto-shortposities), net short positions, prospectuses,
public offers. Each register row carries the date (with time), the issuer as the register names it, the subject and the register detail page.
The pages are Sitecore lists: the first page of results renders server-side (the paged list beyond it is JavaScript — HITL note for a bulk export).
Read-by: 'AFM notification register (afm.nl, per issuer keyword)'. Register rows are the issuer's own record: exempt from the name rule."""
import re
from common import *
BASE = 'https://www.afm.nl'
REGS = [('openbaarmaking-voorwetenschap', 'ad_hoc', 'inside information'), ('financiele-verslaggeving', 'results', 'financial reporting'), ('bestuurders-commissarissen', 'directors_dealings', "directors' and supervisory board transactions"), ('substantiele-deelnemingen-en-bruto-shortposities', 'major_holder', 'substantial holdings'), ('netto-shortposities-actueel', 'short_position', 'net short positions'), ('goedgekeurde-prospectussen', 'prospectus', 'approved prospectuses'), ('openbare-biedingen', 'takeover', 'public offers')]
ROW = re.compile(r'<tr class="jq_registers_register-paged-list_results_tr">(.*?)</tr>', re.S)
CELL = re.compile(r'<td[^>]*>(.*?)</td>', re.S)
MON_NL = {'jan': 1, 'feb': 2, 'mrt': 3, 'mar': 3, 'apr': 4, 'mei': 5, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'okt': 10, 'oct': 10, 'nov': 11, 'dec': 12}
def clean(x): return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', x))).strip()
def nl_date(s):
    m = re.search(r'(\d{1,2}) ([a-z]{3}) (20\d\d)', s.lower())
    return f'{m.group(3)}-{MON_NL.get(m.group(2), 0):02d}-{int(m.group(1)):02d}' if m and MON_NL.get(m.group(2)) else to_iso(s)
def fetch(r):
    evs = []; seen = set(); pages = 0; kw = (r.get('full_name') or r['name'])
    kw = re.sub(r'\b(N\.?V\.?|B\.?V\.?|S\.?E\.?|SE|NV|Koninklijke|Royal)\b\.?', '', kw, flags=re.I).strip(' ,.-')
    for slug, et, label in REGS:
        x = get(f'{BASE}/en/sector/registers/meldingenregisters/{slug}', params={'KeyWords': kw, 'date-from': SINCE.strftime('%d-%m-%Y'), 'date-till': TODAY.strftime('%d-%m-%Y')}, timeout=60)
        if x is None or x.status_code != 200: continue
        pages += 1
        for row in ROW.findall(x.text):
            cells = CELL.findall(row)
            if len(cells) < 2: continue
            link = re.search(r'href="([^"]+)"', cells[0]); dt = nl_date(clean(cells[0])); who = clean(cells[1]); subj = clean(cells[2]) if len(cells) > 2 else ''
            if not link or not dt: continue
            if not name_in(who, r['name'], (r.get('full_name'),)) and not name_in(subj, r['name'], (r.get('full_name'),)): continue
            u = BASE + html.unescape(link.group(1)).split('&KeyWords')[0]
            if u in seen or not in_window(dt): continue
            seen.add(u)
            evs.append(event(r, classify(subj, default=et) if et in ('ad_hoc', 'results') else et, dt, (subj or label)[:300], f'AFM register — {label}', u, 'AFM notification register (afm.nl, per issuer keyword)', wire='AFM', detail=f'register: {label}; issuer as registered: {who}', category=label, language='nl' if slug != 'openbaarmaking-voorwetenschap' else ''))
    return {'events': evs, 'n': len(evs), 'registers_read': pages}
issuers = load_issuers()
if __name__ == '__main__':
    run_workers('afm_events', fetch, issuers, threads=3)
