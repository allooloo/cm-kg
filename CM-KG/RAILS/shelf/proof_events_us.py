r"""SHELF-01 proof (Events, us): the last 30 days of listings and delistings in us-cm-kg's lifecycle index against the exchanges' own notices as EDGAR's
daily form index lists them (www.sec.gov/Archives/edgar/daily-index/<year>/QTR<q>/form.<yyyymmdd>.idx — documented, public): the exchange's
certification of a class for listing (CERT…, filed by NYSE / Nasdaq / Cboe) and the exchange's notice of removal (25-NSE), plus the issuer's own
Form 25 and 8-A12B. Compared per CIK and date for the issuers on the us roster (a fund or note issuer not on the roster is out of scope, counted apart).
Usage: python -X utf8 -I proof_events_us.py [days=30]"""
import os, sys, json, re, time, datetime, collections, requests
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, '..', 'isin-dis')]
import store
UA = {'User-Agent': 'Allooloo Technologies Corp. developers@allooloo.ai'}
days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
import store as _s; _f = _s.bj(_s.cont('us'), 'door/facts.json'); _asof = ((_f.get('nodes') or {}).get('us-cm-kg') or {}).get('as_of')
end = datetime.date.fromisoformat(_asof) - datetime.timedelta(days=1); start = end - datetime.timedelta(days=days - 1)   # the window ends the day before the record's market date: a notice filed after the sweep is not on the record yet
FORMS = {'listing': re.compile(r'^(8-A12B|8-A12G)(/A)?$|^CERT'), 'delisting': re.compile(r'^25(-NSE)?(/A)?$')}
c = store.cont('us'); ix = store.bj(c, 'door/events-by-type.json'); idx = store.bj(c, 'door/index.json')
# the roster's CIKs: from the records' identity (cik) — read through the index keys' record files would be 7,600 reads; the events index carries the cmr,
# and each record names its CIK; read only the records the comparison touches
def cik_of(k):
    try: return str(int(store.bj(c, f"door/records/{k.split('/')[1]}/{k.split('/', 2)[2]}.json")['identity']['cik']['value']))
    except Exception: return None
ours = collections.defaultdict(set)
for t in ('listing', 'delisting'):
    for e in ix['types'][t]:
        if start.isoformat() <= (e['date'] or '') <= end.isoformat(): ours[t].add((e['cmr'], e['date'], (e.get('title') or '').split(' — ')[0]))
# EDGAR's daily form index, every business day in the window
edgar = collections.defaultdict(set); d = start
while d <= end:
    if d.weekday() < 5:
        q = (d.month - 1) // 3 + 1; u = f'https://www.sec.gov/Archives/edgar/daily-index/{d.year}/QTR{q}/form.{d.strftime("%Y%m%d")}.idx'
        r = requests.get(u, headers=UA, timeout=60); time.sleep(0.2)
        if r.status_code == 200:
            for line in r.text.splitlines():
                m = re.match(r'^(\S+(?: \S+)?)\s{2,}(.+?)\s{2,}(\d+)\s{2,}(\d{8})\s{2,}', line)
                if not m: continue
                form, cik, date = m.group(1).strip(), m.group(3), f'{m.group(4)[:4]}-{m.group(4)[4:6]}-{m.group(4)[6:]}'
                for t, pat in FORMS.items():
                    if pat.match(form): edgar[t].add((cik, date, form))
    d += datetime.timedelta(days=1)
# roster CIKs: every us record's CIK (one pass over the CMR keys the EDGAR side names would need a CIK->key map; the live us workbook carries it)
cikmap = {}
for t in ours:
    for k, dt, f in ours[t]:
        if k not in cikmap: cikmap[k] = cik_of(k)
ours_c = {t: {(cikmap.get(k), dt, f) for k, dt, f in ours[t]} for t in ours}
roster_ciks = {v for v in cikmap.values() if v}
# EDGAR rows for CIKs on the roster: the roster's full CIK list comes from the SEC exchange list the node reads (company_tickers_exchange.json)
lst = requests.get('https://www.sec.gov/files/company_tickers_exchange.json', headers=UA, timeout=60).json(); f = lst['fields']
listed = {str(x[f.index('cik')]) for x in lst['data'] if x[f.index('exchange')] in ('NYSE', 'Nasdaq', 'CBOE', 'TXSE')}
out = {'window': [start.isoformat(), end.isoformat()], 'source': 'EDGAR daily form index (exchange CERT… / 25-NSE notices; issuer 8-A12B / 25)'}
for t in ('listing', 'delisting'):
    e_all = edgar[t]; e_roster = {x for x in e_all if x[0] in listed or x[0] in roster_ciks}   # on the exchange list today, or a record of ours (a removed issuer leaves the SEC list)
    o = ours_c.get(t, set())
    match = e_roster & o; miss = sorted(e_roster - o)[:15]; extra = sorted(o - e_roster)[:15]
    out[t] = {'edgar_all_filers': len(e_all), 'edgar_listed_issuers': len(e_roster), 'ours': len(o), 'matched': len(match), 'edgar_not_in_ours': len(e_roster - o), 'ours_not_in_edgar': len(o - e_roster),
              'count_match': len(e_roster) == len(o) == len(match), 'examples_missing': miss, 'examples_extra': extra}
print(json.dumps({k: (v if k not in ('listing', 'delisting') else {kk: vv for kk, vv in v.items() if not kk.startswith('examples')}) for k, v in out.items()}, indent=1))
json.dump(out, open(os.path.join(HERE, f'proof-events-us-{datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%MZ")}.json'), 'w'), indent=1)
