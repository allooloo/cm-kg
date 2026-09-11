"""NSX company announcements from the exchange's public RSS feed (https://www.nsx.com.au/ftp/rss/nsx_rss_announcements.xml — the feed holds the
recent announcements only; each item carries the issuer code in its title, the headline, the date and the announcement page link) and the
official-list feed for listing dates. Read-by: 'nsx.com.au company news feed (exchange feed)'. The exchange feed is the issuer's own listing
(matched on the NSX code in the item title): exempt from the name rule. Writes one row per NSX issuer."""
import re, html
from common import *
def items(url):
    x = get(url, timeout=60)
    if x is None or x.status_code != 200: return []
    out = []
    for it in re.findall(r'<item>(.*?)</item>', x.text, re.S):
        t = html.unescape(re.search(r'<title>(.*?)</title>', it, re.S).group(1)) if re.search(r'<title>', it) else ''
        link = re.search(r'<link>(.*?)</link>', it); pub = re.search(r'<pubDate>(.*?)</pubDate>', it)
        desc = html.unescape(re.sub(r'<[^>]+>', ' ', re.search(r'<description>(.*?)</description>', it, re.S).group(1))) if re.search(r'<description>', it) else ''
        out.append({'title': t.strip(), 'link': link.group(1).strip() if link else '', 'date': to_iso(pub.group(1).strip()) if pub else '', 'desc': re.sub(r'\s+', ' ', desc).strip()[:300]})
    return out
NEWS = items('https://www.nsx.com.au/ftp/rss/nsx_rss_announcements.xml')
def fetch(r):
    if r['exchange'] != 'NSX': return {'gap': 'not an NSX issuer', 'events': []}
    evs = []
    for it in NEWS:
        m = re.match(r'\[(\w+)\]\s*(.*)', it['title'])
        if not m or m.group(1).upper() != str(r['ticker']).upper() or not it['link'].startswith('http') or not in_window(it['date']): continue
        head = m.group(2).strip(); sensitive = bool(re.search(r'(?i)\(price sensitive\)', head)); head = re.sub(r'(?i)\s*\(price sensitive\)\s*', '', head).strip()
        evs.append(event(r, classify(head, default='nsx_announcement'), it['date'], head, 'NSX company announcements feed', it['link'], 'nsx.com.au company news feed (exchange feed)', wire='NSX', asx_category=head, price_sensitive='true' if sensitive else 'false', detail='price sensitive' if sensitive else ''))
    return {'events': evs, 'n': len(evs), 'feed_items': len(NEWS), 'note': 'the NSX feed carries recent announcements only' if evs else 'no item for this code in the current feed'}
issuers = load_issuers()
if __name__ == '__main__':
    print('NSX feed items', len(NEWS), flush=True)
    run_workers('nsx_events', fetch, issuers, threads=4)
