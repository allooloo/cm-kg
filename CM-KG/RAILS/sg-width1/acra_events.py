"""ACRA register events from the monthly bulk dataset (data.gov.sg, read from the Width 0 pond drop acra_pub.jsonl by UEN): the annual return date
(a dated register filing: 'annual_return'), and a status other than Live (status change; the file carries the current status only, so the event is
dated on the dataset build date and says so). Former names carry no date in the dataset: they are noted, never dated. URL = the public BizFile entry
(unverified by fetch). Read-by: 'ACRA register bulk dataset (data.gov.sg, monthly)'. Registry rows are the issuer's own record: exempt from the name rule."""
from common import *
ACRA = {}
for d in pond.read_jsonl_all(NODE, 'width0', 'acra_pub.jsonl', key='uen'): ACRA[d['uen']] = d
META = pond.read_json_latest(NODE, 'width0', 'acra_index_meta.json') or {}
RB = 'ACRA register bulk dataset (data.gov.sg, monthly)'
def fetch(r):
    a = ACRA.get(r.get('uen') or '')
    if not a: return {'gap': 'no UEN / ACRA row in Width 0', 'events': []}
    evs = []; src = a['src']
    ar = to_iso(a.get('annual_return_date', ''))
    if in_window(ar): evs.append(event(r, 'annual_return', ar, 'Annual return filed (ACRA)', 'ACRA register', src, RB, detail=f"UEN {a['uen']}"))
    if a.get('status') and not a['status'].lower().startswith('live'):
        evs.append(event(r, 'status_change', META.get('built', TODAY.isoformat()), f"ACRA status: {a['status']}", 'ACRA register', src, RB, detail=f"UEN {a['uen']}; the bulk file carries the current status only — dated on the dataset build date"))
    note = f"{len(a['former_names'])} former name(s) on the register, undated in the dataset: " + ' | '.join(a['former_names'][:3]) if a.get('former_names') else ''
    return {'events': evs, 'n': len(evs), 'note': note}
issuers = load_issuers()
if __name__ == '__main__':
    run_workers('acra_events', fetch, issuers, threads=8)
