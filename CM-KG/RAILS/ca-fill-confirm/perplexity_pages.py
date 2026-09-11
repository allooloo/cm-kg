"""Pass 2.7 — Perplexity (sonar-pro, grounded) finds the issuer's current release page on its wire for the issuers whose
wire company page was missing or stale in Width 1. The answer is verified by fetching the page and checking it names the
issuer; unverified answers go to Gaps. Label: 'read by Perplexity (agent)'. The page name found becomes a sourced alias."""
import re
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
wp = {d['key']: d for d in jload(W1 + r'\wire_pages.jsonl')}
targets = [byk[k] for k, d in wp.items() if k in byk and (d.get('gap', '').endswith('not found') or (d.get('page') and not d.get('n')))]
def fetch(r):
    q = (f"Find the official press-release listing page for the company \"{r['name']}\" ({r['exchange']}: {r['ticker']}) on a newswire site "
         f"(newswire.ca, prnewswire.com, newsfilecorp.com, globenewswire.com, businesswire.com, accesswire.com, thenewswire.com). "
         f"Reply with JSON only: {{\"url\": \"<the company's own release listing page URL, or empty>\", \"display_name\": \"<company name as shown on that page>\", \"wire\": \"<wire>\"}}")
    res = perplexity(q)
    j = jparse(res.get('text', '')) or {}
    url = (j.get('url') or '').strip(); ok = False; shown = ''
    if url.startswith('http') and any(w in url for w in ['newswire.ca', 'prnewswire.com', 'newsfilecorp.com', 'globenewswire.com', 'businesswire.com', 'accesswire.com', 'accessnewswire.com', 'thenewswire.com']):
        t, st = page_text(url)
        if t and (name_match(t[:3000], r['name'])[0] in ('full', 'distinctive') or (j.get('display_name') and norm(j['display_name']) in norm(t[:3000]))): ok = True; shown = j.get('display_name', '')
    return {'url': url, 'verified': ok, 'display_name': shown, 'wire': j.get('wire', ''), 'citations': res.get('citations', [])[:5], 'usage': res.get('usage'), 'error': res.get('error')}
if __name__ == '__main__':
    print('targets', len(targets), flush=True)
    resume('perplexity_pages', fetch, targets, threads=4)
