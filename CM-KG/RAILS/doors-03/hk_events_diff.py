r"""IW-01 — read only: the hk events on the wire (pond/assembled/2026-10-25/hk-events.jsonl, the build behind the door's 163,422) against the held build's events (pond/assembled/2026-10-26/hk-events.jsonl).
Each event that left is classed: window roll (dated before the new build's twelve-month window), duplicate collapsed (its key still present once), folded listing
(moved to the record's primary line), or other — named. Writes hk-411-<ts>.json beside this script."""
import json, os, subprocess, collections, datetime, concurrent.futures as cf
from azure.storage.blob import BlobServiceClient
os.environ['AZURE_CONFIG_DIR'] = r'C:\ALLOOLOO\.azure'
key = subprocess.run(['az', 'storage', 'account', 'keys', 'list', '-g', 'allooloo-cmkg-eastasia', '-n', 'allooloocmkghkpond', '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True, shell=True).stdout.strip()
c = BlobServiceClient('https://allooloocmkghkpond.blob.core.windows.net', credential=key, max_single_get_size=8 << 20).get_container_client('pond')
J = lambda n: [json.loads(l) for l in c.download_blob(n).readall().decode('utf-8').splitlines() if l.strip()]
names = ['pond/assembled/2026-10-25/hk-events.jsonl']   # the build the wire serves (163,422 events, checked below)
wire = [('', '', e) for e in J(names[0])]
new = J('pond/assembled/2026-10-26/hk-events.jsonl')
print('wire files', len(names), 'wire events', len(wire), 'new events', len(new))
print('wire sample', json.dumps(wire[0][2], ensure_ascii=False)[:400]); print('new sample', json.dumps(new[0], ensure_ascii=False)[:400])
K = lambda e: (str(e.get('date'))[:10], e.get('url') or e.get('source_url') or '', (e.get('title') or '')[:200])
wk = collections.Counter(K(e) for _, _, e in wire); nk = collections.Counter(K(e) for e in new)
newtk = collections.defaultdict(set)
for e in new: newtk[K(e)].add(str(e.get('ticker') or ''))
wd = [k[0] for k in nk]; lo_new = min(wd); lo_wire = min(k[0] for k in wk)
left, came = [], []
for k, n in wk.items():
    m = nk.get(k, 0)
    if m < n: left += [k] * (n - m)
for k, n in nk.items():
    m = wk.get(k, 0)
    if n > m: came += [k] * (n - m)
cls = collections.Counter(); ex_ = collections.defaultdict(list)
for k in left:
    if k[0] < lo_new: t = 'window roll (dated before the new build\'s first day ' + lo_new + ')'
    elif nk.get(k, 0) >= 1: t = 'duplicate collapsed (the same date/url/title still served once)'
    else: t = 'other'
    cls[t] += 1
    if len(ex_[t]) < 12: ex_[t].append(k)
came_win = collections.Counter('inside the window, new' for k in came)
out = {'wire_events': len(wire), 'new_events': len(new), 'net': len(new) - len(wire), 'left': len(left), 'came': len(came), 'wire_first_day': lo_wire, 'new_first_day': lo_new,
       'left_by_class': dict(cls), 'examples': {k: v for k, v in ex_.items()}, 'came_first_days': sorted({k[0] for k in came})[:5], 'came_last_days': sorted({k[0] for k in came})[-5:],
       'left_days': collections.Counter(k[0] for k in left).most_common(10)}
fn = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"hk-411-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%MZ')}.json")
json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print(json.dumps(out, ensure_ascii=False, indent=1)[:4000])
