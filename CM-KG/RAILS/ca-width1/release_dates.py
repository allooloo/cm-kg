"""Dates for search-found releases that carried none (Newsfile, Accesswire, TheNewswire, and any other wire hit without a date):
fetch the release page and read the date it prints. Read-by: 'release page date'. No date on the page = no event (it goes to Gaps)."""
import re, html, json
from common import *
MONTHS = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
def page_date(u, txt):
    if 'newsfilecorp.com' in u:
        m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', txt) or re.search(r'(' + MONTHS + r' \d{1,2}, 20\d\d)', txt)
        return to_iso(m.group(1)) if m else ''
    if 'accesswire.com' in u or 'accessnewswire.com' in u:
        m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', txt) or re.search(r'(' + MONTHS + r' \d{1,2}, 20\d\d)', txt)
        return to_iso(m.group(1)) if m else ''
    if 'thenewswire.com' in u:
        t = html.unescape(re.sub(r'<[^>]+>', ' ', txt))
        m = re.search(r'\((' + MONTHS + r' \d{1,2}, 20\d\d)\)\s*[–—-]\s*TheNewswire', t) or re.search(r'TheNewswire\s*[–—-]\s*(' + MONTHS + r' \d{1,2}, 20\d\d)', t) or re.search(r'(' + MONTHS + r' \d{1,2}, 20\d\d)\s*[–—-]\s*TheNewswire', t)
        return to_iso(m.group(1)) if m else ''
    m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', txt) or re.search(r'article:published_time"\s+content="([^"]+)"', txt)
    return to_iso(m.group(1)) if m else ''
def main():
    items = {}
    for line in open('raw/wire_search.jsonl', encoding='utf-8'):
        d = json.loads(line)
        for u in d.get('undated', []): items.setdefault(u['url'], {'key': d['key'], **u})
    iss = {key(r): r for r in load_issuers()}
    rows = [{'exchange': v['key'].split('|')[0], 'ticker': v['key'].split('|')[1], 'url': u, 'title': v['title'], 'wire': v['wire']} for u, v in items.items()]
    def fetch(it):
        r = iss.get(it['exchange'] + '|' + it['ticker'])
        x = get(it['url'], tries=2, timeout=40)
        if x is None or x.status_code != 200: return {'url': it['url'], 'gap': f'release page http {x.status_code if x else "none"}', 'events': []}
        date = page_date(it['url'], x.text)
        if not date: return {'url': it['url'], 'gap': 'no date printed on release page', 'events': []}
        if not in_window(date): return {'url': it['url'], 'events': [], 'note': 'outside window'}
        return {'url': it['url'], 'events': [event(r, classify(it['title']), date, it['title'], it['wire'], it['url'], 'Tavily search (wire domains) + release page date', wire=it['wire'])]}
    # key by URL for resume
    fn_out = 'raw/release_dates.jsonl'; done = set()
    if os.path.exists(fn_out):
        for line in open(fn_out, encoding='utf-8'):
            try: done.add(json.loads(line)['url'])
            except Exception: pass
    skip = [s for s in os.environ.get('SKIP_DOMAINS', '').split(',') if s]
    todo = [it for it in rows if it['url'] not in done and not any(s in it['url'] for s in skip)]; print('release_dates todo', len(todo), 'done', len(done), 'skipping domains', skip, flush=True)
    delay = float(os.environ.get('DELAY', '0'))
    out = open(fn_out, 'a', encoding='utf-8'); cnt = [0]
    def work(it):
        if delay: time.sleep(delay)
        try: res = fetch(it)
        except Exception as e: res = {'url': it['url'], 'error': repr(e)[:200], 'events': []}
        res['key'] = it['exchange'] + '|' + it['ticker']
        with lock:
            out.write(json.dumps(res, ensure_ascii=False) + '\n'); out.flush(); cnt[0] += 1
            if cnt[0] % 100 == 0: print('release_dates', cnt[0], '/', len(todo), flush=True)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '8'))) as ex: list(ex.map(work, todo))
    print('release_dates DONE', flush=True)
if __name__ == '__main__': main()
