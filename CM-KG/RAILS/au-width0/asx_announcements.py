"""Step 3 — ASX announcements platform per issuer (public search page, no login):
   https://www.asx.com.au/asx/v2/statistics/announcements.do?by=asxCode&asxCode=<code>&timeframe=Y&year=<yyyy>
Kept: the number of announcements over the last 12 months (the ASX platform is every listed entity's primary channel), the latest announcement
headed "Annual Report" (or Appendix 4E and Annual Report) with its viewer link (…/displayAnnouncement.do?display=pdf&idsId=<id>), and the latest
announcement date. Read-by: 'asx.com.au announcements search (exchange site)'. Writes raw/asx_announcements.jsonl keyed by code."""
import requests, json, os, re, time, threading, html, datetime
from concurrent.futures import ThreadPoolExecutor
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
TODAY = datetime.date.today(); SINCE = TODAY - datetime.timedelta(days=365)
codes = [x['ASX code'] for x in json.load(open('raw/asx_directory.json', encoding='utf-8'))]
done = set()
if os.path.exists('raw/asx_announcements.jsonl'):
    for line in open('raw/asx_announcements.jsonl', encoding='utf-8'):
        try: done.add(json.loads(line)['code'])
        except Exception: pass
todo = [c for c in codes if c not in done]; print('todo', len(todo), 'done', len(done), flush=True)
out = open('raw/asx_announcements.jsonl', 'a', encoding='utf-8'); lock = threading.Lock(); cnt = [0]
ROW = re.compile(r'<tr[^>]*>(.*?)</tr>', re.S)
def parse(h):
    rows = []
    for r in ROW.findall(h):
        d = re.search(r'(\d{2})/(\d{2})/(20\d\d)', r); a = re.search(r'idsId=(\d+)', r)
        if not (d and a): continue
        cells = [html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', c))).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)]
        head = next((c for c in cells if c and not re.match(r'^\d{2}/\d{2}/\d{4}', c) and not re.fullmatch(r'[\d:]+ [ap]m|\d+ pages?|[\d.]+[KM]B|\*?', c)), '')
        rows.append({'date': f'{d.group(3)}-{d.group(2)}-{d.group(1)}', 'headline': head[:200], 'idsId': a.group(1), 'url': f'https://www.asx.com.au/asx/v2/statistics/displayAnnouncement.do?display=pdf&idsId={a.group(1)}'})
    return rows
def work(c):
    rec = {'code': c, 'query': f'https://www.asx.com.au/asx/v2/statistics/announcements.do?by=asxCode&asxCode={c}&timeframe=Y&year={TODAY.year}'}
    rows = []
    for y in (TODAY.year, TODAY.year - 1):
        for attempt in range(4):
            try:
                r = requests.get('https://www.asx.com.au/asx/v2/statistics/announcements.do', params={'by': 'asxCode', 'asxCode': c, 'timeframe': 'Y', 'year': y}, headers=UA, timeout=60)
                if r.status_code in (429, 502, 503): time.sleep(5 * (attempt + 1)); continue
                if r.status_code == 200: rows += parse(r.text)
                else: rec[f'http_{y}'] = r.status_code
                break
            except Exception: time.sleep(3)
        time.sleep(0.2)
    rows = [x for x in rows if x['date'] >= SINCE.isoformat()]
    rec['n_12m'] = len(rows); rec['latest_date'] = max((x['date'] for x in rows), default='')
    ar = [x for x in rows if re.search(r'(?i)annual report|annual financial report', x['headline']) and not re.search(r'(?i)notice|update|corrected|amend|presentation', x['headline'])]
    if ar: rec['annual_report'] = ar[0]
    with lock:
        out.write(json.dumps(rec, ensure_ascii=False) + '\n'); out.flush(); cnt[0] += 1
        if cnt[0] % 100 == 0: print(cnt[0], '/', len(todo), flush=True)
with ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '4'))) as ex: list(ex.map(work, todo))
print('DONE', flush=True)
