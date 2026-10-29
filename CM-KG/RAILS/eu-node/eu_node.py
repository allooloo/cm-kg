r"""eu_node.py — NODE-EU-01…14 (DAY ORDER 4, 2026-10-24): one European node from its official sources, on the Hong Kong pattern, pond-native.
Inputs per market (written by the source research, CM-KG\RAILS\eu-sources\<cc>\): roster.py fetch() (ESMA FIRDS / the exchange's list: ISIN, name, MIC, LEI,
ticker) and events.py fetch(isin_or_issuer, since) (the national regulated-information store). Outputs, the shape load_nodes.py reads for the ISIN-keyed
Euronext nodes (France, Netherlands):
  POND\<cc>-cm-kg\width0\<date>\roster.json · width1\<date>\events.jsonl     (dated, immutable drops)
  POND\<cc>-cm-kg\assembled\<date>\<cc>-issuers.xlsx (one tab per venue, ticker = ISIN) + <cc>-events.jsonl, mirrored to CM-KG\ISSUERS and CM-KG\DISCLOSURE\events
Every field carries its source and read-by; blank stays blank. Usage: python -X utf8 eu_node.py <cc> [--days 365] [--events-limit N]"""
import os, sys, json, datetime, importlib.util, shutil, time
from concurrent.futures import ThreadPoolExecutor
import openpyxl
ROOT = os.environ.get('CMKG_ROOT', r'C:\ALLOOLOO'); RAILS = os.path.join(ROOT, 'CM-KG', 'RAILS'); HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); import pond   # the pond helper, one copy per rails folder
CC = sys.argv[1]; NODE = f'{CC}-cm-kg'; DAYS = int(sys.argv[sys.argv.index('--days') + 1]) if '--days' in sys.argv else 365
LIMIT = int(sys.argv[sys.argv.index('--events-limit') + 1]) if '--events-limit' in sys.argv else None
VENUES = json.load(open(os.path.join(HERE, 'venues.json'), encoding='utf-8'))[CC]   # {MIC: the exchange's official name — the record's Exchange field}
try: TABS = json.load(open(os.path.join(HERE, 'tabs.json'), encoding='utf-8')).get(CC) or {}   # CEO tab rule 2026-10-24: 'Country — Stock Exchange' / 'Country — CODE'
except Exception: TABS = {}
def mod(name):
    p = os.path.join(RAILS, 'eu-sources', CC, name + '.py')
    if not os.path.exists(p): p = os.path.join(RAILS, 'row-sources', CC, name + '.py')   # NODE-ROW (DAY ORDER 5, 2026-10-24)
    s = importlib.util.spec_from_file_location(f'{CC}_{name}', p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def main():
    today = datetime.date.today().isoformat(); since = (datetime.date.today() - datetime.timedelta(days=DAYS)).isoformat()
    ro = mod('roster').fetch(); rows = [r for r in ro['rows'] if r.get('isin') and r.get('mic') in VENUES]
    seen, roster = set(), []
    for r in rows:
        if r['isin'] in seen: continue
        seen.add(r['isin']); roster.append(r)
    d0 = pond.open_drop(NODE, 'width0'); json.dump({**{k: ro.get(k) for k in ('source_url', 'read_by', 'read_at')}, 'rows': roster}, open(os.path.join(d0, 'roster.json'), 'w', encoding='utf-8'), ensure_ascii=False); pond.close_drop(NODE, 'width0')
    log(NODE, 'roster', len(roster), 'of', ro.get('count'), 'rows on', sorted(VENUES))
    ev = mod('events'); events, errs = [], 0
    def one(r):
        try: return r, ev.fetch(r['isin'], since) or []
        except Exception as e: return r, e
    todo = roster[:LIMIT] if LIMIT else roster
    with ThreadPoolExecutor(6) as ex:
        for r, out in ex.map(one, todo):
            if isinstance(out, Exception): errs += 1; continue
            for e in out:
                if not e.get('date') or not e.get('url'): continue
                events.append({'exchange': VENUES[r['mic']], 'ticker': r['isin'], 'date': str(e['date'])[:10], 'event_type': e.get('type') or 'regulatory_filing', 'title': e.get('title'), 'url': e['url'],
                               'source': e.get('source'), 'read_by': e.get('source') or 'the regulated-information store', 'state': 'sourced', 'category': e.get('type')})
    d1 = pond.open_drop(NODE, 'width1')
    with open(os.path.join(d1, 'events.jsonl'), 'w', encoding='utf-8') as f:
        for e in events: f.write(json.dumps(e, ensure_ascii=False) + '\n')
    pond.close_drop(NODE, 'width1'); log(NODE, 'events', len(events), 'for', len({e['ticker'] for e in events}), 'issuers · read errors', errs)
    out = pond.assembled(NODE); wb = openpyxl.Workbook(); wb.remove(wb.active)
    HDR = ['Legal name', 'ISIN', 'Exchange', 'MIC', 'CFI', 'Ticker', 'LEI', 'LEI source', 'LEI read by', 'LEI State', 'Roster source', 'Roster read by', 'ISIN source', 'ISIN read by', 'ISIN State', 'Gaps']
    for mic, tab in VENUES.items():
        ws = wb.create_sheet(TABS.get(mic, tab)[:31]); ws.append(HDR)   # the sheet carries the short tab name; the Exchange column keeps the official name
        for r in (x for x in roster if x['mic'] == mic):
            gaps = [] if r.get('lei') else ['LEI: the roster carries none']
            ws.append([r.get('name'), r['isin'], tab, mic, r.get('cfi'), r.get('ticker'), r.get('lei'), ro.get('source_url') if r.get('lei') else None, ro.get('read_by') if r.get('lei') else None, 'sourced' if r.get('lei') else None,
                       ro.get('source_url'), ro.get('read_by'), ro.get('source_url'), ro.get('read_by'), 'sourced', ' | '.join(gaps) or None])
    xp = os.path.join(out, f'{CC}-issuers.xlsx'); wb.save(xp)
    # the assembled event set = every earlier assembled event + tonight's read, deduped on (ISIN, date, URL): a three-day nightly window never shrinks the door
    prev = pond.latest_assembled(NODE, f'{CC}-events.jsonl') if hasattr(pond, 'latest_assembled') else None
    allev, seen_e = [], set()
    for src in ([prev] if prev and os.path.dirname(prev) != out else []) + [os.path.join(d1, 'events.jsonl')]:
        for line in open(src, encoding='utf-8'):
            e = json.loads(line); k = (e['ticker'], e['date'], e['url'])
            if k in seen_e: continue
            seen_e.add(k); allev.append(e)
    events = allev
    ep = os.path.join(out, f'{CC}-events.jsonl')
    with open(ep, 'w', encoding='utf-8') as f:
        for e in allev: f.write(json.dumps(e, ensure_ascii=False) + chr(10))
    os.makedirs(os.path.join(ROOT, 'CM-KG', 'ISSUERS'), exist_ok=True); os.makedirs(os.path.join(ROOT, 'CM-KG', 'DISCLOSURE', 'events'), exist_ok=True)
    for src, dst in ((xp, os.path.join(ROOT, 'CM-KG', 'ISSUERS', f'{CC}-issuers.xlsx')), (ep, os.path.join(ROOT, 'CM-KG', 'DISCLOSURE', 'events', f'{CC}-events.jsonl'))):
        if os.path.exists(dst): shutil.copyfile(dst, dst + '.pre-' + datetime.datetime.now().strftime('%Y%m%dT%H%M%S'))
        shutil.copyfile(src, dst)
    json.dump({'node': NODE, 'built': today, 'roster': len(roster), 'events': len(events), 'issuers_with_events': len({e['ticker'] for e in events}), 'read_errors': errs, 'venues': VENUES, 'since': since}, open(os.path.join(out, 'build.json'), 'w'), indent=1)
    log(NODE, 'assembled', out)
if __name__ == '__main__': main()
