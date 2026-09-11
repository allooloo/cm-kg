"""Pass 2.4 — Gemini (gemini-flash-latest, long context) reads each issuer's 12-month RNS set — every cached body in full, plus the headline of every
other announcement — for issuers with no agm_record_date event, and for issuers with no registrar, and returns any annual/general meeting date or
record date a release STATES (with the announcement URL) and any registrar a release names. A meeting/record finding becomes an agm_record_date event
dated on the announcement date (the stated date goes in Detail); a registrar finding is written to the issuer record with the citing URL. Label: 'read by Gemini'."""
import hashlib
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
rows = {r['_tab'] + '|' + r['Ticker (TIDM)']: r for r in all_rows()}
EV = events(); have = set(e['exchange'] + '|' + e['ticker'] for e in EV if e['event_type'] == 'agm_record_date')
by_iss = {}
for e in EV:
    if 'Companies House' in e.get('read_by', ''): continue
    by_iss.setdefault(e['exchange'] + '|' + e['ticker'], []).append(e)
def body_of(url):
    fn = 'raw/bodies/' + hashlib.sha1(url.encode()).hexdigest() + '.txt'
    return open(fn, encoding='utf-8').read() if os.path.exists(fn) else ''
def fetch(r):
    k = key(r); evs = by_iss.get(k, [])
    if not evs: return {'skip': 'no announcements in the window', 'findings': [], 'registrar': ''}
    parts = []; nbody = 0
    for e in sorted(evs, key=lambda x: x['date']):
        b = body_of(e['url'])
        if b: nbody += 1; parts.append(f"### {e['date']} | {e['title']} | {e['url']}\n{b[:12000]}")
        else: parts.append(f"### {e['date']} | {e['title']} | {e['url']}\n(headline only)")
    text = '\n\n'.join(parts)[:300000]
    need_reg = not (rows.get(k, {}).get('Registrar') or '')
    prompt = (f"Issuer: {r['name']} ({r['exchange']}: {r['ticker']}). Below are this issuer's regulatory announcements over the last 12 months (some with full text, some headline only).\n"
              "Task 1: find every statement of an annual general meeting or general meeting DATE, and every RECORD DATE for such a meeting or for a dividend, that an announcement explicitly states. Do not infer.\n"
              + ("Task 2: name the share registrar if any announcement states it (e.g. 'Computershare Investor Services PLC', 'Equiniti', 'MUFG Corporate Markets', 'Neville Registrars', 'Share Registrars Limited'), with the announcement URL.\n" if need_reg else "")
              + "Return JSON: {\"findings\": [{\"release_url\": \"...\", \"release_date\": \"YYYY-MM-DD\", \"kind\": \"agm|general_meeting|record_date\", \"stated_date\": \"YYYY-MM-DD\", \"evidence\": \"verbatim sentence\"}], \"registrar\": \"<name or empty>\", \"registrar_url\": \"<announcement URL or empty>\", \"registrar_evidence\": \"<verbatim or empty>\"}. Empty list / empty strings if none.\n\n" + text)
    res = gemini(prompt); j = jparse(res.get('text', '')) or {}
    return {'findings': j.get('findings', []) if isinstance(j, dict) else [], 'registrar': (j.get('registrar') or '') if isinstance(j, dict) else '', 'registrar_url': (j.get('registrar_url') or '') if isinstance(j, dict) else '', 'registrar_evidence': (j.get('registrar_evidence') or '') if isinstance(j, dict) else '',
            'n_releases': len(evs), 'n_bodies': nbody, 'usage': res.get('usage'), 'error': res.get('error')}
if __name__ == '__main__':
    targets = [r for r in issuers if by_iss.get(key(r)) and (key(r) not in have or not (rows.get(key(r), {}).get('Registrar') or ''))]
    print('issuers to read (no AGM event or no registrar, with announcements):', len(targets), flush=True)
    resume('gemini_agm', fetch, targets, threads=int(E.get('THREADS', '6')))
