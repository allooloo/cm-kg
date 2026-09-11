"""Pass 2.7 — Mistral (mistral-small-latest) reads any non-English announcement in the UK 12-month set (title language detected from the headline:
Welsh, French, German, Spanish, Italian, Dutch stop-word test) for period end / meeting dates. On the UK the count is expected to be zero; the
worker reports the count it found and reads exactly those, no padding. Label: 'read by Mistral'."""
import hashlib
from fc_common import *
EV = events()
NON_EN = re.compile(r"(?i)\b(résultats|rapport annuel|assemblée générale|jahresabschluss|hauptversammlung|ergebnisse|resultados|junta general|risultati|assemblea|jaarverslag|algemene vergadering|cyfarfod cyffredinol|adroddiad blynyddol)\b")
targets = [e for e in EV if NON_EN.search(e.get('title', ''))]
def body_of(url):
    fn = 'raw/bodies/' + hashlib.sha1(url.encode()).hexdigest() + '.txt'
    return open(fn, encoding='utf-8').read() if os.path.exists(fn) else ''
def fetch(e):
    b = body_of(e['url']) or page_text(e['url'])[0] or ''
    if len(b) < 300: return {'url': e['url'], 'gap': 'no body'}
    prompt = (f"Announcement by {e['issuer']} dated {e['date']}: {e['title']}\n\nTEXT:\n{b[:14000]}\n\nExtract, only if stated: period_end (YYYY-MM-DD), meeting_date (YYYY-MM-DD), record_date (YYYY-MM-DD), auditor. "
              'Reply JSON: {"period_end": "", "meeting_date": "", "record_date": "", "auditor": "", "evidence": ""}')
    res = mistral(prompt); j = jparse(res.get('text', '')) or {}
    return {'url': e['url'], **j, 'usage': res.get('usage'), 'error': res.get('error')}
if __name__ == '__main__':
    print('non-English announcements found:', len(targets), flush=True)
    resume('mistral_reads', fetch, targets, threads=3, keyf=lambda e: e['url'])
    json.dump({'n_targets': len(targets)}, open('raw/mistral_count.json', 'w'))
