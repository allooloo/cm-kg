"""Pass 2.4 — Gemini (gemini-flash-latest, long context) reads each issuer's 12-month release set — every fetched body in full,
plus the title and indexed snippet of every other release — for issuers with no agm_record_date event, and returns any
annual/special meeting date or record date a release STATES, with the release URL. A finding becomes an agm_record_date event
dated on the release date (the meeting/record date itself goes in Detail). Label: 'read by Gemini'."""
import hashlib
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
EV = events(); have = set(e['exchange'] + '|' + e['ticker'] for e in EV if e['event_type'] == 'agm_record_date')
by_iss = {}
for e in EV: by_iss.setdefault(e['exchange'] + '|' + e['ticker'], []).append(e)
def body_of(url):
    fn = 'raw/bodies/' + hashlib.sha1(url.encode()).hexdigest() + '.txt'
    return open(fn, encoding='utf-8').read() if os.path.exists(fn) else ''
def fetch(r):
    evs = by_iss.get(key(r), [])
    if not evs: return {'skip': 'no releases in the window', 'findings': []}
    parts = []; nbody = 0
    for e in sorted(evs, key=lambda x: x['date']):
        b = body_of(e['url'])
        if b: nbody += 1; parts.append(f"### {e['date']} | {e['title']} | {e['url']}\n{b[:12000]}")
        else: parts.append(f"### {e['date']} | {e['title']} | {e['url']}\n(body not fetched; title only)")
    text = '\n\n'.join(parts)[:300000]
    prompt = (f"Issuer: {r['name']} ({r['exchange']}: {r['ticker']}). Below are this issuer's releases over the last 12 months (some with full text, some title only).\n"
              "Task: find every statement of an annual general meeting, annual and special meeting, or special meeting DATE, and every RECORD DATE for such a meeting, "
              "that a release explicitly states. Do not infer. Return JSON: {\"findings\": [{\"release_url\": \"...\", \"release_date\": \"YYYY-MM-DD\", \"kind\": \"agm|special_meeting|record_date\", \"stated_date\": \"YYYY-MM-DD\", \"evidence\": \"verbatim sentence\"}]}. Empty list if none.\n\n" + text)
    res = gemini(prompt)
    j = jparse(res.get('text', '')) or {}
    return {'findings': j.get('findings', []) if isinstance(j, dict) else [], 'n_releases': len(evs), 'n_bodies': nbody, 'usage': res.get('usage'), 'error': res.get('error')}
if __name__ == '__main__':
    targets = [r for r in issuers if key(r) not in have and by_iss.get(key(r))]
    print('issuers without an AGM/record-date event but with releases:', len(targets), flush=True)
    resume('gemini_agm', fetch, targets, threads=int(E.get('THREADS', '6')))
