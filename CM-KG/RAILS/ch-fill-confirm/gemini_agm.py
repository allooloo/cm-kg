"""Pass 2.4 — Gemini (gemini-flash-latest, long context) reads each issuer's 12-month announcement set (headlines with dates and links; exchange headlines are
the category names, so the read is over the headline set plus any cached results announcements text) for issuers with no agm_record_date event or no share
registry, and returns meeting / record dates an announcement STATES and any registry named. Label: 'read by Gemini'."""
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
rows = {r['_tab'] + '|' + r['Symbol']: r for r in all_rows()}
EV = events(); have = set(e['exchange'] + '|' + e['ticker'] for e in EV if e['event_type'] == 'agm_egm')
by_iss = {}
for e in EV:
    if 'Zefix' in e.get('read_by', ''): continue
    by_iss.setdefault(e['exchange'] + '|' + e['ticker'], []).append(e)
docs = {}
if os.path.isdir('raw/reports'):
    for f in os.listdir('raw/reports'):
        d = json.load(open('raw/reports/' + f, encoding='utf-8')); docs.setdefault(d.get('key'), []).append(d)
def fetch(r):
    k = key(r); evs = by_iss.get(k, [])
    if not evs: return {'skip': 'no announcements in the window', 'findings': [], 'registrar': ''}
    parts = [f"### {e['date']} | {e['title']} | {e['url']}" for e in sorted(evs, key=lambda x: x['date'])]
    for d in docs.get(k, [])[:2]:
        parts.append(f"### DOCUMENT {d.get('kind')} {d.get('date')} {d.get('pdf_url') or d.get('viewer')}\n" + '\n'.join((d.get('registry_windows') or [])[:2] + (d.get('period_windows') or [])[:1])[:8000])
    text = '\n'.join(parts)[:300000]; need_reg = not (rows.get(k, {}).get('Share registrar') or '')
    prompt = (f"Issuer: {r['name']} ({r['exchange']}: {r['ticker']}). Below are this issuer's EQS News / SIX ad hoc over the last 12 months (date | headline | link) and excerpts of its lodged documents.\n"
              "Task 1: find every annual general meeting or general meeting DATE and every RECORD DATE (meeting or dividend) an announcement or excerpt explicitly states. Do not infer from the headline alone.\n"
              + ("Task 2: name the share registrar if an excerpt states it (e.g. 'Boardroom Corporate & Advisory Services Pte. Ltd.', 'Tricor Barbinder Share Registration Services', 'M & C Services Private Limited', 'B.A.C.S. Private Limited', 'KCK CorpServe Pte. Ltd.', 'In.Corp Corporate Services'), with the document link.\n" if need_reg else "")
              + "Return JSON: {\"findings\": [{\"release_url\": \"...\", \"release_date\": \"YYYY-MM-DD\", \"kind\": \"agm|general_meeting|record_date\", \"stated_date\": \"YYYY-MM-DD\", \"evidence\": \"verbatim\"}], \"registrar\": \"<name or empty>\", \"registrar_url\": \"<link or empty>\", \"registrar_evidence\": \"<verbatim or empty>\"}. Empty list / empty strings if none.\n\n" + text)
    res = gemini(prompt); j = jparse(res.get('text', '')) or {}
    return {'findings': j.get('findings', []) if isinstance(j, dict) else [], 'registrar': (j.get('registrar') or '') if isinstance(j, dict) else '', 'registrar_url': (j.get('registrar_url') or '') if isinstance(j, dict) else '', 'registrar_evidence': (j.get('registrar_evidence') or '') if isinstance(j, dict) else '',
            'n_releases': len(evs), 'usage': res.get('usage'), 'error': res.get('error')}
if __name__ == '__main__':
    targets = [r for r in issuers if by_iss.get(key(r)) and (key(r) not in have or not (rows.get(key(r), {}).get('Share registrar') or ''))]
    print('issuers to read:', len(targets), flush=True)
    resume('gemini_agm', fetch, targets, threads=int(E.get('THREADS', '6')))
