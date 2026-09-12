"""Pass 2.7 — Mistral (mistral-small-latest) reads any non-English announcement in the AU 12-month set (headline language test). Chinese-language releases are the
expected case on Switzerland; the worker reports the count it found and reads exactly those, no padding. Label: 'read by Mistral (zh)'."""
from fc_common import *
EV = events()
NON_EN = re.compile(r"(?i)\b(résultats|rapport annuel|assemblée générale|jahresabschluss|hauptversammlung|ergebnisse|resultados|junta general|risultati|assemblea|jaarverslag)\b|[\u4e00-\u9fff]{2,}")
targets = [e for e in EV if (e.get('language') or '') in ('de', 'fr', 'it') or NON_EN.search(e.get('title', ''))]  # German / French / Italian items: Mistral reads them natively (label 'read by Mistral (de/fr)')
def fetch(e):
    t, st = page_text(e['url'])
    if not t or len(t) < 300: return {'url': e['url'], 'gap': 'no body'}
    prompt = (f"Announcement by {e['issuer']} dated {e['date']}: {e['title']}\n\nTEXT:\n{t[:14000]}\n\nExtract, only if stated: period_end (YYYY-MM-DD), meeting_date (YYYY-MM-DD), record_date (YYYY-MM-DD), auditor. "
              'Reply JSON: {"period_end": "", "meeting_date": "", "record_date": "", "auditor": "", "evidence": ""}')
    res = mistral(prompt); j = jparse(res.get('text', '')) or {}
    return {'url': e['url'], **j, 'usage': res.get('usage'), 'error': res.get('error'), 'read_by': 'read by Mistral (de/fr)'}
if __name__ == '__main__':
    print('non-English announcements found:', len(targets), flush=True)
    resume('mistral_reads', fetch, targets[:int(E.get('MISTRAL_MAX', '600'))], threads=4, keyf=lambda e: e['url'])
    json.dump({'n_targets': len(targets)}, open('raw/mistral_count.json', 'w'))
