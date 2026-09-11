"""Regulatory announcements (RNS and the other regulatory information services) per issuer from Investegate's public per-company listing:
   https://www.investegate.co.uk/company/<TIDM>?page=N      (50 announcements per page, newest first; paged back to the window start)
Investegate answers plain HTTP clients (HTTP 200); the LSE's own news list loads through a component call the pages API does not expose,
and the FCA NSM refuses machines, so this is the RNS source of record for the rail. Each row: announcement date, RIS source code
(RNS, GNW = GlobeNewswire, PRN = PR Newswire, BUS = Business Wire, ...), RNS headline, announcement URL.
rns_category = the RNS headline as published (Investegate's Announcement column). Event type from the headline (common.classify).
Read-by: 'investegate.co.uk company page (RNS mirror)'. Company-page reads are the issuer's own listing (exempt from the name rule)."""
import re, html
from common import *
SRC = {'RNS': 'RNS', 'GNW': 'GlobeNewswire', 'PRN': 'PR Newswire', 'BUS': 'Business Wire', 'ACW': 'ACCESS Newswire', 'EQS': 'EQS Group', 'MSC': 'Marketscreener', 'PRA': 'PR Newswire', 'RNSNR': 'RNS Non-Regulatory', 'DJN': 'Dow Jones Newswires', 'GLOBE': 'GlobeNewswire', 'NFC': 'Newsfile', 'UKREG': 'UK Regulatory'}
ROW = re.compile(r'<tr[^>]*>(.*?)</tr>', re.S)
def parse(h):
    out = []
    for row in ROW.findall(h):
        d = re.search(r'(\d{2} [A-Z][a-z]{2} 20\d\d)', row)
        a = re.search(r'href="(https?://www\.investegate\.co\.uk/announcement/[^"]+)"[^>]*>(.*?)</a>', row, re.S)
        if not (d and a): continue
        s = re.search(r'/source/([A-Za-z0-9]+)', row)
        title = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', a.group(2)))).strip()
        out.append({'date': to_iso(d.group(1)), 'source': (s.group(1).upper() if s else ''), 'title': title, 'url': a.group(1).split('?')[0]})
    return out
def fetch(r):
    t = r['ticker']; evs = []; page = 1; seen = set(); oldest = ''; pages = 0
    while page <= 30:
        u = f'https://www.investegate.co.uk/company/{t}' + (f'?page={page}' if page > 1 else '')
        x = get(u, timeout=60)
        if x is None: return {'gap': 'Investegate company page: no response', 'events': evs}
        if x.status_code == 404: return {'gap': f'Investegate has no company page for TIDM {t}', 'events': []}
        if x.status_code != 200: return {'gap': f'Investegate company page HTTP {x.status_code}', 'events': evs}
        rows = parse(x.text); pages += 1
        if not rows: break
        for it in rows:
            if not it['date'] or it['url'] in seen: continue
            seen.add(it['url']); oldest = it['date']
            if not in_window(it['date']): continue
            wire = SRC.get(it['source'], it['source'] or 'RNS')
            evs.append(event(r, classify(it['title']), it['date'], it['title'], f'Regulatory announcement via Investegate ({it["source"] or "RNS"})', it['url'], 'investegate.co.uk company page (RNS mirror)', wire=wire, rns_category=it['title'], detail=f'RIS source {it["source"] or "RNS"}'))
        if oldest and oldest < SINCE.isoformat(): break
        if 'rel="next"' not in x.text: break
        page += 1
    return {'events': evs, 'n': len(evs), 'pages': pages, 'page': f'https://www.investegate.co.uk/company/{t}'}
issuers = load_issuers()
if __name__ == '__main__':
    run_workers('investegate', fetch, issuers, threads=int(os.environ.get('THREADS', '4')))
