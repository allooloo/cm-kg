"""Companies House filings per issuer (issuers with a Companies House number from Width 0), via the REST API with the key in AGENT KEYS:
   GET https://api.company-information.service.gov.uk/company/<number>/filing-history?items_per_page=100&start_index=N
Each filing in the window becomes an event: date = the filing date on the register; title = the registry's description (with its description values
folded in where they carry a date or a name); URL = the filing's document page on the public site; ch_filing_type = the registry category;
detail = the form type code. Read-by: 'Companies House REST API (filing history)'. Rate limit 600 per five minutes."""
import re, json
from common import *
if not CH_KEY: raise SystemExit('no Companies House key file — filings not available (HITL)')
API = 'https://api.company-information.service.gov.uk'
calls = [0]; window = [time.time()]
def api(path, **params):
    with lock:
        if calls[0] >= 560:
            wait = 300 - (time.time() - window[0])
            if wait > 0: time.sleep(wait)
            calls[0] = 0; window[0] = time.time()
        calls[0] += 1
    for attempt in range(5):
        try:
            r = requests.get(API + path, params=params, auth=(CH_KEY, ''), timeout=60)
            if r.status_code == 429: time.sleep(30); continue
            if r.status_code == 404: return None
            r.raise_for_status(); return r.json()
        except Exception:
            time.sleep(3 * (attempt + 1))
    return None
def describe(it):
    d = (it.get('description') or '').replace('-', ' ')
    dv = it.get('description_values') or {}
    extras = [str(v) for k, v in dv.items() if k in ('made_up_date', 'new_date', 'officer_name', 'new_name', 'old_name', 'change_date', 'charge_number', 'date', 'appointment_date', 'termination_date', 'cessation_date') and not isinstance(v, (list, dict))]
    return d + ((' — ' + '; '.join(extras)) if extras else '')
def fetch(r):
    if not r.get('ch_number'): return {'gap': 'no Companies House number in Width 0 (see uk-issuers Gaps)', 'events': []}
    num = r['ch_number']; evs = []; start = 0; total = None; pages = 0
    while True:
        j = api(f'/company/{num}/filing-history', items_per_page=100, start_index=start)
        if j is None: return {'gap': f'filing history HTTP 404 for {num}', 'events': []} if start == 0 else {'events': evs, 'n': len(evs), 'note': 'filing history paging stopped early'}
        total = j.get('total_count', 0); items = j.get('items') or []; pages += 1
        oldest = ''
        for it in items:
            date = to_iso(it.get('date')); oldest = date or oldest
            if not in_window(date): continue
            cat = it.get('category') or 'other'; et, ftype = CH_CATEGORY.get(cat, ('ch_other', cat))
            tid = it.get('transaction_id') or ''
            url = f'https://find-and-update.company-information.service.gov.uk/company/{num}/filing-history/{tid}/document?format=pdf&download=0' if tid else f'https://find-and-update.company-information.service.gov.uk/company/{num}/filing-history'
            title = describe(it)
            if cat == 'change-of-name':
                dv = it.get('description_values') or {}
                if dv.get('new_name') or dv.get('old_name'): title = f"change of name: {dv.get('old_name') or ''} → {dv.get('new_name') or ''}".strip()
            evs.append(event(r, et, date, title, 'Companies House', url, 'Companies House REST API (filing history)', detail=f"form {it.get('type') or ''}; category {cat}", ch_filing_type=ftype))
        start += 100
        if not items or start >= total or (oldest and oldest < SINCE.isoformat()) or pages > 15: break
    return {'events': evs, 'n': len(evs), 'total_filings': total, 'pages': pages, 'number': num}
issuers = load_issuers()
if __name__ == '__main__':
    run_workers('ch_filings', fetch, issuers, threads=int(os.environ.get('THREADS', '3')))
