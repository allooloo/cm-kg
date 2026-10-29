"""LENS-01 — GraphQL httpRequests1dGroups, prior 30 days, daily, UTC, every active zone in the account. Read-only.
The API allows at most 10 zones per query ("too many zones requested" above that), so: batches of 10, a few threads, throttled under the 300-per-5-minutes quota."""
import json, urllib.request, time, datetime, threading, concurrent.futures as cf
SP = r'C:\Users\matth\AppData\Local\Temp\claude\C--bpc-agent\4fc1172b-aaae-4859-9f0f-29f4a875d910\scratchpad'
T = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare-analytics.txt').read().strip()
H = {'Authorization': 'Bearer ' + T, 'Content-Type': 'application/json'}
today = datetime.date(2026, 10, 28)
d_geq = (today - datetime.timedelta(days=30)).isoformat(); d_lt = today.isoformat()   # 2026-09-28 .. 2026-10-27 inclusive = 30 days
zones = json.load(open(f'{SP}/zones_all.json', encoding='utf-8'))['zones']
ids = [z['id'] for z in zones]
Q_DAILY = '''query($tags:[string!],$geq:Date!,$lt:Date!){viewer{zones(filter:{zoneTag_in:$tags}){zoneTag
 httpRequests1dGroups(limit:31,filter:{date_geq:$geq,date_lt:$lt},orderBy:[date_ASC]){dimensions{date}
 sum{requests cachedRequests bytes cachedBytes threats pageViews encryptedRequests responseStatusMap{edgeResponseStatus requests}} uniq{uniques}}}}}'''
Q_COUNTRY = '''query($tags:[string!],$geq:Date!,$lt:Date!){viewer{zones(filter:{zoneTag_in:$tags}){zoneTag
 httpRequests1dGroups(limit:1,filter:{date_geq:$geq,date_lt:$lt}){sum{countryMap{clientCountryName requests}}}}}}'''
lock = threading.Lock(); last = [0.0]; GAP = 1.1   # ~55 queries a minute, under the 300 / 5 min quota
def gql(q, tags):
    body = json.dumps({'query': q, 'variables': {'tags': tags, 'geq': d_geq, 'lt': d_lt}}).encode()
    err = ''
    for attempt in range(5):
        with lock:
            w = last[0] + GAP - time.time()
            if w > 0: time.sleep(w)
            last[0] = time.time()
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request('https://api.cloudflare.com/client/v4/graphql', data=body, headers=H), timeout=120))
            if r.get('errors'): raise RuntimeError(json.dumps(r['errors'])[:300])
            return r['data']['viewer']['zones']
        except Exception as e:
            err = repr(e)[:300]; time.sleep(10 * (attempt + 1))
    raise RuntimeError(err)
daily = {}; country = {}; failed = {}; done = [0]
def work(batch):
    out = {}
    try:
        for z in gql(Q_DAILY, batch): out[z['zoneTag']] = ('d', z['httpRequests1dGroups'])
    except Exception as e:
        for t in batch: out[t] = ('fail', repr(e)[:200])
    try:
        for z in gql(Q_COUNTRY, batch):
            t = z['zoneTag']; country[t] = (z['httpRequests1dGroups'][0]['sum']['countryMap'] if z['httpRequests1dGroups'] else [])
    except Exception as e:
        for t in batch: country.setdefault(t, []); failed.setdefault(t, 'country read: ' + repr(e)[:200])
    with lock:
        for t, (k, v) in out.items():
            if k == 'd': daily[t] = v
            else: failed[t] = v
        done[0] += len(batch)
        if done[0] % 200 < len(batch): print(done[0], 'zones', len(failed), 'failed', time.strftime('%H:%M:%S'), flush=True)
batches = [ids[i:i + 10] for i in range(0, len(ids), 10)]
with cf.ThreadPoolExecutor(4) as ex: list(ex.map(work, batches))
missing = [t for t in ids if t not in daily and t not in failed]
json.dump({'window': [d_geq, d_lt], 'read_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'daily': daily, 'country': country, 'failed': failed, 'missing_in_response': missing},
          open(f'{SP}/traffic_raw.json', 'w', encoding='utf-8'))
print('done', len(daily), 'with data', len(failed), 'failed', len(missing), 'absent from response')
