"""ASX announcements per issuer from the ASX announcements platform's public search page (no login):
   https://www.asx.com.au/asx/v2/statistics/announcements.do?by=asxCode&asxCode=<code>&timeframe=Y&year=<yyyy>
Each row: date and time, the price-sensitive marker (the "pricesens" cell carries the ASX marker image when the announcement was flagged),
headline, viewer link (…/displayAnnouncement.do?display=pdf&idsId=<id>). asx_category = the headline as published (the ASX category names —
Appendix 4E/4D, Appendix 4C/5B, Trading Halt, Becoming a substantial holder, Appendix 3Y, Appendix 3B, Dividend/Distribution, Notice of Meeting, …
are the headlines). Event type from the headline (common.classify). Read-by: 'asx.com.au announcements search (exchange site)'.
The ASX per-company page data is the issuer's own listing: exempt from the name rule."""
import re, html
from common import *
ROW = re.compile(r'<tr[^>]*>(.*?)</tr>', re.S)
def parse(h):
    rows = []
    for r in ROW.findall(h):
        d = re.search(r'(\d{2})/(\d{2})/(20\d\d)', r); a = re.search(r'idsId=(\d+)', r)
        if not (d and a): continue
        ps = re.search(r'<td class="pricesens"[^>]*>(.*?)</td>', r, re.S)
        sensitive = bool(ps and re.search(r'<img|\$|price', ps.group(1), re.I))
        cells = [html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', c))).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)]
        head = next((c for c in cells if c and not re.match(r'^\d{2}/\d{2}/\d{4}', c) and not re.fullmatch(r'[\d:]+ [ap]m|\d+ pages?|[\d.]+[KM]B|\*?', c)), '')
        rows.append({'date': f'{d.group(3)}-{d.group(2)}-{d.group(1)}', 'headline': head[:200], 'idsId': a.group(1), 'sensitive': sensitive, 'url': f'https://www.asx.com.au/asx/v2/statistics/displayAnnouncement.do?display=pdf&idsId={a.group(1)}'})
    return rows
def fetch(r):
    if r['exchange'] != 'ASX': return {'gap': 'not an ASX issuer', 'events': []}
    evs = []; seen = set(); years = sorted(set([TODAY.year, SINCE.year]), reverse=True); pages = 0
    for y in years:
        x = get('https://www.asx.com.au/asx/v2/statistics/announcements.do', params={'by': 'asxCode', 'asxCode': r['ticker'], 'timeframe': 'Y', 'year': y}, timeout=60)
        if x is None: return {'gap': 'ASX announcements search: no response', 'events': evs}
        if x.status_code != 200: return {'gap': f'ASX announcements search HTTP {x.status_code}', 'events': evs}
        pages += 1
        for it in parse(x.text):
            if it['url'] in seen or not in_window(it['date']): continue
            seen.add(it['url'])
            evs.append(event(r, classify(it['headline']), it['date'], it['headline'], 'ASX announcements platform', it['url'], 'asx.com.au announcements search (exchange site)', wire='ASX', asx_category=it['headline'], price_sensitive='true' if it['sensitive'] else 'false', detail='price sensitive' if it['sensitive'] else ''))
        time.sleep(0.2)
    return {'events': evs, 'n': len(evs), 'pages': pages, 'page': f"https://www.asx.com.au/markets/trade-our-cash-market/announcements/{r['ticker']}"}
issuers = load_issuers()
if __name__ == '__main__':
    run_workers('asx_events', fetch, issuers, threads=int(os.environ.get('THREADS', '4')))
