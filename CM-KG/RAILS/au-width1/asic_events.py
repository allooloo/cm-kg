"""ASIC register events from the weekly bulk dataset (data.gov.au Company Dataset), read from the Width 0 pond drop (asic_pub.jsonl):
name changes (a previous-name row's 'until' date = the date the current name started), deregistration (Date of Deregistration), and a status
other than REGD (status change; the bulk file carries the current status only, so the event is dated on the dataset's publication month and
says so). URL = the public ASIC Connect search entry for the ACN (unverified by fetch; the ASIC Connect API needs a key — HITL).
Read-by: 'ASIC company register bulk dataset (data.gov.au, weekly)'. Registry rows are the issuer's own record: exempt from the name rule."""
import re
from common import *
ASIC = {}
for d in pond.read_jsonl_all(NODE, 'width0', 'asic_pub.jsonl', key='acn'): ASIC[d['acn']] = d
META = pond.read_json_latest(NODE, 'width0', 'asic_index_meta.json') or {}
def fetch(r):
    a = ASIC.get(r.get('acn') or '')
    if not a: return {'gap': 'no ACN / ASIC row in Width 0', 'events': []}
    evs = []; src = a['src']
    for p in a.get('previous_names', []):
        dt = to_iso(p.get('until', ''))
        if in_window(dt): evs.append(event(r, 'name_change', dt, f"change of name: {p['name']} → {a['name']}", 'ASIC company register', src, 'ASIC company register bulk dataset (data.gov.au, weekly)', detail=f"ACN {a['acn']}; former name {p['name']} until {dt}"))
    dr = to_iso(a.get('deregistered', ''))
    if in_window(dr): evs.append(event(r, 'status_change', dr, 'deregistration', 'ASIC company register', src, 'ASIC company register bulk dataset (data.gov.au, weekly)', detail=f"ACN {a['acn']}; status {a.get('status')}"))
    if a.get('status') and a['status'] != 'REGD':
        evs.append(event(r, 'status_change', META.get('built', TODAY.isoformat()), f"ASIC status {a['status']}", 'ASIC company register', src, 'ASIC company register bulk dataset (data.gov.au, weekly)', detail=f"ACN {a['acn']}; current status on the dataset published {META.get('file', '')} — the bulk file carries no status-change date"))
    return {'events': evs, 'n': len(evs)}
issuers = load_issuers()
if __name__ == '__main__':
    run_workers('asic_events', fetch, issuers, threads=8)
