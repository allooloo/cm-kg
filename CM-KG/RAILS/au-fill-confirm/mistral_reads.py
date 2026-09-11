"""Pass 2.7 — Mistral (mistral-small-latest) reads any non-English announcement in the AU 12-month set (headline language test). Expected zero on
Australia; the worker reports the count it found and reads exactly those, no padding. Label: 'read by Mistral'."""
from fc_common import *
EV = events()
NON_EN = re.compile(r"(?i)\b(résultats|rapport annuel|assemblée générale|jahresabschluss|hauptversammlung|ergebnisse|resultados|junta general|risultati|assemblea|jaarverslag|年度报告|年报|股东大会)\b")
targets = [e for e in EV if NON_EN.search(e.get('title', ''))]
def fetch(e):
    t, st = page_text(e['url'])
    if not t or len(t) < 300: return {'url': e['url'], 'gap': 'no body'}
    prompt = (f"Announcement by {e['issuer']} dated {e['date']}: {e['title']}\n\nTEXT:\n{t[:14000]}\n\nExtract, only if stated: period_end (YYYY-MM-DD), meeting_date (YYYY-MM-DD), record_date (YYYY-MM-DD), auditor. "
              'Reply JSON: {"period_end": "", "meeting_date": "", "record_date": "", "auditor": "", "evidence": ""}')
    res = mistral(prompt); j = jparse(res.get('text', '')) or {}
    return {'url': e['url'], **j, 'usage': res.get('usage'), 'error': res.get('error')}
if __name__ == '__main__':
    print('non-English announcements found:', len(targets), flush=True)
    resume('mistral_reads', fetch, targets, threads=3, keyf=lambda e: e['url'])
    json.dump({'n_targets': len(targets)}, open('raw/mistral_count.json', 'w'))
