r"""ORDER-037 (2026-10-23) — the Allooloo nightly digest and the Saturday sweepREVIEW roll-up, on the apex image (cmkg-sweep), run by two triggers of the apex:
  cmkg-apex-digest   20 14 * * *  UTC   after the 14:00 UTC Issuerwire close: one row per agent (the twelve nodes, the apex, the eight Issuerwire rails) —
                                         agent · as_of · verdict · rows · delta · flags · hand items — plus spend per lab and the Tavily meter.
                                         Writes ops/<night>/DIGEST-<night>.md + ops/<night>/digest.json and ops/mail/<night>.json (the Logic App
                                         allooloo-ops-digest fires on that blob and sends one email to developers@allooloo.ai). Private store only:
                                         allooloocmkgapex/ops (allooloo-cmkg-shared, public blob access off). Never on a public surface.
  cmkg-apex-week     0 13,14 * * 6 UTC  MODE=week; runs only in the hour that is 06:00 Saturday in Los Angeles (13:00 UTC in daylight time, 14:00 UTC in
                                         standard time; the other fire logs "not 06:00 Pacific" and exits 0): sweepREVIEW-WEEK-<date>.md from the last
                                         seven digests — seven nights per agent, every FAIL and the night it cleared, hand items, the week's spend, the X line
                                         STAGED (never posted) — human-half fields on top; to ops/week/ and beside the nightly sweepREVIEW in sweeps/<date>/.
Reads only: node markers sweeps/<night>/<cc>/{done,failed,skipped}.json, the apex marker sweeps/<night>/apex-done.json, and the Issuerwire markers
ops/<night>/<job>/{done,failed}.json in stgamnfrc/pond (GSC tenant) through the read + list SAS in secret issuerwire-pond-sas. Pond rule: a second write of
the same night lands beside (-2 ...), never over."""
import os, sys, json, re, datetime, subprocess, traceback
from azure.storage.blob import BlobServiceClient, ContainerClient, ContentSettings
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
# ENUM-01 (DAY ORDER 6, 2026-10-25): the nodes are the roster of record (apex nodes.json / list_nodes) — no list of its own here; store region = region.store
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import roster   # -I drops the script folder from the path
NODES = [(roster.cc_of(n), (n.get('region') or {}).get('store')) for n in roster.load()]
# the Issuerwire rails (Allooloo product, run in the GSC tenant, rg-amn-frc) and the field that counts each one's rows
IW = [('standing', 'checked'), ('filings', 'landed'), ('coverage', 'pages_checked'), ('claims', 'listed'), ('receipts', 'ledger_events'), ('ark', 'objects_written'), ('stores', 'news_landed'), ('close', 'rows_signed')]
MODE = os.environ.get('MODE', 'daily'); FORCE = os.environ.get('FORCE', '0') == '1'
APEX_SA = os.environ.get('APEX_STORAGE_ACCOUNT', 'allooloocmkgapex'); OPS = os.environ.get('OPS_CONTAINER', 'ops'); SWEEPS = os.environ.get('APEX_CONTAINER', 'sweeps')
T0 = datetime.datetime.now(datetime.timezone.utc); NIGHT = os.environ.get('NIGHT') or T0.date().isoformat()
EXEC = os.environ.get('CONTAINER_APP_JOB_EXECUTION_NAME', os.environ.get('HOSTNAME', '?')); IMAGE_TAG = os.environ.get('IMAGE_TAG', '?')
if not os.environ.get('DRY_DIR'): os.environ.setdefault('AZURE_CONFIG_DIR', '/tmp/.azure')
os.environ['AZURE_CORE_COLLECT_TELEMETRY'] = 'false'
LOG = []
def log(*a):
    s = f"{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')} " + ' '.join(str(x) for x in a); print(s, flush=True); LOG.append(s)
def az(*a, raw=False):
    p = subprocess.run(['az', *a] + ([] if raw else ['-o', 'json']) + (['--subscription', SUB] if os.environ.get('DRY_DIR') and a[:1] == ('storage',) and '--subscription' not in a else []), capture_output=True, text=True, encoding='utf-8', errors='replace', shell=os.name == 'nt')
    if p.returncode != 0: raise RuntimeError(f"az {' '.join(a[:4])} failed: {(p.stderr or p.stdout)[-400:]}")
    return p.stdout.strip() if raw else (json.loads(p.stdout) if p.stdout.strip() else None)
def client(sa, key, cont): return BlobServiceClient(f'https://{sa}.blob.core.windows.net', credential=key).get_container_client(cont)
def get_json(c, name):
    if DRY_DIR and os.path.exists(os.path.join(DRY_DIR, c.container_name, name)): return json.load(open(os.path.join(DRY_DIR, c.container_name, name), encoding='utf-8'))
    try: return json.loads(c.get_blob_client(name).download_blob().readall().decode('utf-8'))
    except Exception: return None
DRY_DIR = os.environ.get('DRY_DIR')   # laptop test: read the live markers with the signed-in az, write the outputs under DRY_DIR, no blob written
def put_beside(c, name, data, ct):
    """pond rule: the first write of a night takes the name; a re-run lands beside as name-2, name-3 ..."""
    if DRY_DIR:
        p = os.path.join(DRY_DIR, c.container_name, name); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'wb').write(data.encode('utf-8') if isinstance(data, str) else data); return p
    n, i = name, 1
    while c.get_blob_client(n).exists(): i += 1; n = f'{name}-{i}'
    c.upload_blob(n, data.encode('utf-8') if isinstance(data, str) else data, content_settings=ContentSettings(content_type=ct)); return n
def clean(s): return str(s).replace('Â·', '·').replace('Â', '') if s is not None else s   # the node markers carry a double-encoded middle dot
def pacific_now(t):
    """Los Angeles wall clock without tzdata: daylight time from the second Sunday of March 02:00 to the first Sunday of November 02:00 (local)."""
    y = t.year
    mar = datetime.datetime(y, 3, 8, tzinfo=datetime.timezone.utc); mar += datetime.timedelta(days=(6 - mar.weekday()) % 7)
    nov = datetime.datetime(y, 11, 1, tzinfo=datetime.timezone.utc); nov += datetime.timedelta(days=(6 - nov.weekday()) % 7)
    dst = mar + datetime.timedelta(hours=10) <= t < nov + datetime.timedelta(hours=9)   # 02:00 PST = 10:00 UTC; 02:00 PDT = 09:00 UTC
    return t + datetime.timedelta(hours=-7 if dst else -8), dst

def hand_items(d):
    """a hand item is any field that names the CEO's hand (HITL) or a door held for the machine half's explanation"""
    out = []
    for k, v in (d or {}).items():
        if isinstance(v, str) and 'HITL' in v: out.append(f'{k}: {clean(v)[:160]}')
    return out
def spend_of(lines):
    """spend lines -> {lab: usd} from the '$x.xx' figure on each line; the lab is the line's second segment ('<run> · <lab> (<model>) · ...');
    reads-only lines ('no lab') and the United States job's unmetered line are kept apart; lines without a figure count with 0"""
    labs = {}
    for l in lines or []:
        l = clean(l); seg = [x.strip() for x in l.split(' · ')]; lab = (seg[1] if len(seg) > 1 else 'other').split(' (')[0]
        if 'no lab' in l: lab = 'no lab (reads only)'
        elif lab.startswith('United States job'): lab = 'United States job (not metered here)'
        elif lab.startswith('AWS'): lab = 'AWS'
        usd = sum(float(m) for m in re.findall(r'\$([\d.]+)', l))
        e = labs.setdefault(lab, {'usd': 0.0, 'lines': 0}); e['usd'] = round(e['usd'] + usd, 4); e['lines'] += 1
    return labs

DOORS = [('getasof.ai', 'get_as_of', {'issuer': 'NASDAQ:MSFT', 'as_of': '2023-03-15'}), ('getfilings.ai', 'get_filings', {'issuer': 'NASDAQ:MSFT', 'from': '2026-10-01'}),
         ('getauditor.ai', 'get_auditor', {'issuer': 'NASDAQ:AAPL'}), ('getticker.ai', 'get_ticker', {'identifier': 'MSFT', 'exchange': 'NASDAQ'}),
         ('gettargetmarket.ai', 'get_target_market', {'subject': 'TEST:DE000TMKT025'})]
def door_rows():
    """OPS-06 B2: (agent, group, as_of, verdict, rows, flags, hands) per get_ door; never stops the digest"""
    import requests, base64
    UA = {'User-Agent': 'Allooloo digest (OPS-06 doors)', 'accept': 'application/json'}
    b64d = lambda s: base64.urlsafe_b64decode(s + '=' * (-len(s) % 4)); b64e = lambda b: base64.urlsafe_b64encode(b).decode().rstrip('=')
    def call(u, name, args):
        r = requests.post(u, json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}}, headers=UA, timeout=60)
        j = r.json(); res = j.get('result') or {}
        return r.status_code, (res.get('structuredContent') or (json.loads(res['content'][0]['text']) if res.get('content') else {}) or {'error': j.get('error')})
    try: J = {k['kid']: k for k in requests.get('https://allooloo.ai/.well-known/jwks.json', headers=UA, timeout=30).json()['keys']}
    except Exception as e: J = {}; log('keyring not read:', repr(e)[:120])
    def sig_ok(sc):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        sg = sc.get('signature') or {}; k = J.get(sg.get('kid'))
        if not k: return False, f"kid {sg.get('kid')} not on the keyring"
        body = {a: b for a, b in sc.items() if a not in ('signature', 'receipt')}   # signed over the answer without signature and receipt (keys sorted, compact)
        msg = (sg['protected'] + '.' + b64e(json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())).encode()
        try: Ed25519PublicKey.from_public_bytes(b64d(k['x'])).verify(b64d(sg['signature']), msg); return True, f"kid {sg['kid']}"
        except Exception: return False, f"kid {sg['kid']}: signature does not verify"
    out = []
    for host, tool, args in DOORS:
        fl = []; ok = True; rid = None
        try:
            t0 = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0) - datetime.timedelta(seconds=5)
            pg = requests.get(f'https://{host}/', headers={'User-Agent': UA['User-Agent']}, timeout=30).status_code
            st_, sc = call(f'https://mcp.{host}/mcp', tool, args)
            w = pg == 200 and st_ == 200 and not sc.get('error'); ok &= w
            fl.append(f"wire {pg}/{st_}" + ('' if w else f" ({str(sc.get('error'))[:80]})"))
            if tool == 'get_target_market':
                _, v = call(f'https://mcp.{host}/mcp', 'verify_target_market', {'statement': sc.get('statement') or {}})
                s_ok = v.get('valid') is True and v.get('sig_ok') is True and v.get('node_sig_ok') is True; s_note = f"kid {v.get('sig_kid')} + node {v.get('node_sig_kid')} (verify_target_market)"
            else: s_ok, s_note = sig_ok(sc)
            ok &= s_ok; fl.append(('signature OK · ' if s_ok else 'signature FAIL · ') + s_note)
            rid = (sc.get('receipt') or {}).get('id') or sc.get('receipt_id')
            if rid:
                _, rv = call('https://mcp.rco-records.ai/mcp', 'verify_receipt', {'id': rid})
                ver = rv.get('verification') or {}; ca = (rv.get('receipt') or {}).get('cleared_at') or ''
                valid = bool(ver) and all(v_ is True for k_, v_ in ver.items() if k_.endswith('_ok')) and (rv.get('valid', True) is not False)
                fresh = ca[:19] >= t0.strftime('%Y-%m-%dT%H:%M:%S')
                ok &= valid and fresh; fl.append(f"receipt {rid} · " + ('valid' if valid else 'NOT valid') + ' · ' + (f'fresh (cleared {ca[11:19]}Z)' if fresh else f'NOT fresh (cleared {ca or "—"})'))
            else: ok = False; fl.append('no receipt on the answer')
        except Exception as e: ok = False; fl.append('door not read: ' + repr(e)[:120])
        out.append((host.split('.')[0], 'door', NIGHT, 'PASS' if ok else 'FAIL', None, [f'{tool} · ' + fl[0]] + fl[1:], [] if ok else [f'read the door: https://mcp.{host}/mcp']))
    return out

def state_block(ops, rows, cap):
    """MORNING-01 (2026-11-01): the STATE block, from the wire (the capacity snapshot, tonight's rows, earlier digests) and the orders ledger
    (ops/ledger/<stamp>.json, newest, written at every close by C:/NODES/rail/ledger.py). Returns (state dict, lines). Never stops the digest."""
    st = {'generated_utc': T0.isoformat(timespec='seconds')}; L = None; lname = None
    try:
        names = sorted(b.name for b in ops.list_blobs(name_starts_with='ledger/') if b.name.endswith('.json'))
        if DRY_DIR:
            ld = os.path.join(DRY_DIR, ops.container_name, 'ledger')
            if os.path.isdir(ld): names = sorted(set(names) | {'ledger/' + f for f in os.listdir(ld) if f.endswith('.json')})
        if names: lname = names[-1]; L = get_json(ops, lname)
    except Exception as e: st['ledger_error'] = repr(e)[:160]
    pv = cap.get('provisioned') or {}; snap_tags = sorted({v.get('tag') for v in ((pv.get('jobs') or {}).get('tags') or {}).values() if v.get('repo') == 'cmkg-sweep'})
    st['fleet'] = {'fleet_tag': cap.get('fleet_tag'), 'moved_utc': pv.get('read_utc'), 'snapshot_tags': snap_tags}
    held = []
    for r in rows:
        if r['verdict'] != 'HELD': continue
        since = NIGHT; d0 = datetime.date.fromisoformat(NIGHT)
        for i in range(1, 61):   # walk the earlier digests back while the same agent was HELD
            n = (d0 - datetime.timedelta(days=i)).isoformat(); pr = next((x for x in ((get_json(ops, f'{n}/digest.json') or {}).get('rows') or []) if x['agent'] == r['agent']), None)
            if pr and pr.get('verdict') == 'HELD': since = n
            else: break
        rel = None   # a held build published after tonight's marker (publish_held.py, the CEO's go) leaves a note in the store's door-release/
        try:
            cc = r.get('node'); reg = dict(NODES).get(cc); sa = f'allooloocmkg{cc}pond'
            k = az('storage', 'account', 'keys', 'list', '-n', sa, '-g', f'allooloo-cmkg-{reg}', '--query', '[0].value', '-o', 'tsv', raw=True)
            rel = next(iter(sorted((b.name for b in client(sa, k, 'pond').list_blobs(name_starts_with=f"door-release/{r.get('as_of')}")), reverse=True)), None)
        except Exception as e: log(f'{r["agent"]}: door-release not read', repr(e)[:120])
        held.append({'door': r['agent'], 'since_night': since, 'flag': next((f for f in r['flags'] if f.startswith('HELD')), '')[:200], 'published_since': rel})
    st['held'] = held
    if L:
        st['ledger'] = {'blob': f'{APEX_SA}/{OPS}/{lname}', 'written_utc': L.get('written_utc')}
        st['orders'] = [{'order': o['order'], 'date': o.get('date'), 'close': o.get('close')} for o in L.get('orders') or []]
        # OPS-06 B4 (CEO 2026-11-07): Allooloo hand items only — no GSC-named item (GSC-OPS-FIX-01 and any item naming GSC or gsc-em.com) — and only
        # what the ledger holds open (an item closed by a later report's "hand item closed:" line is not in hand_open)
        gsc = lambda h: str(h.get('order') or '').upper().startswith('GSC') or re.search(r'\bGSC\b|gsc-em\.com', str(h.get('item') or ''))
        st['hand_open'] = [h for h in (L.get('hand_open') or []) if not gsc(h)]; st['hand_dropped_gsc'] = [h.get('order') for h in (L.get('hand_open') or []) if gsc(h)]
        st['jobs_unrun'] = L.get('jobs_unrun') or []; st['jobs_source'] = L.get('jobs_source')
        st['rulings'] = [{'id': x['id'], 'line': x['line']} for x in L.get('rulings_standing') or []]
    f = st['fleet']; lines = ['## STATE', '', f"*Generated {st['generated_utc']} from the wire and the orders ledger" + (f" ({st['ledger']['blob']}, written {st['ledger']['written_utc']})*" if L else ' — the ledger was not read (flag)*'), '']
    tag_note = '' if snap_tags == [f['fleet_tag']] else f" · the snapshot holds {', '.join(snap_tags) or 'no cmkg-sweep tags'} (DRIFT below)"
    lines += [f"- **Fleet tag** {f['fleet_tag']} · moved {str(f['moved_utc'] or 'not read')[:16].replace('T', ' ')} UTC (the capacity snapshot's write date){tag_note}"]
    if not L:
        lines += ['- **Orders, hand items, jobs not yet run, rulings:** not read (flag): no orders ledger under ops/ledger/' + (f" — {st.get('ledger_error')}" if st.get('ledger_error') else '')]
    else:
        lines += ['- **Last orders closed** (newest first):']
        for o in st['orders']:
            c = o.get('close') or {}
            lines.append(f"  - {o['order']} ({o.get('date') or '—'}) · " + (f"DRIFT {c.get('drift')} · pages {c.get('pages_read')} read, {c.get('pages_failed')} failed · www {c.get('www')}" if c else 'no build_nodes run before the report'))
        lines += ['- **Open hand items:** ' + ('none' if not st['hand_open'] else '')]
        lines += [f"  - {h['order']}: {h['item']}" + (f" ({', '.join('AGENT KEYS/' + p for p in h['pastes'])})" if h.get('pastes') else '') for h in st['hand_open']]
        lines += ['- **Jobs with no first run yet** (' + (st.get('jobs_source') or 'ARM') + '): ' + ('none' if not st['jobs_unrun'] else '')]
        for j in st['jobs_unrun']:
            fs = j.get('first_scheduled_utc') or '—'; past = fs[:2] == '20' and fs[:16] < T0.isoformat()[:16]
            lines.append(f"  - {j['job']} ({j['group']}) · cron {j.get('cron') or '—'} · first scheduled {fs.replace('+00:00', ' UTC')}" + (' — passed since the ledger was read; the next close shows whether it ran' if past else ''))
    # OPS-06 B6 (CEO 2026-11-07): the held doors are listed once, in the agents table (their row carries since-night and the go line); no STATE entry
    for h in held:
        r = next((x for x in rows if x['agent'] == h['door']), None)
        if r is not None:
            r['flags'].insert(0, f"held since the {h['since_night']} night" + (f", published since ({h['published_since']}); the next night's marker shows the door" if h.get('published_since') else ''))
    # DIGEST-LINES (CEO 2026-11-05, "One line in the digest"): an order's one line for the night, written by whoever closed it to
    # ops/digest/lines/<night>/<name>.txt; the first line of each file, printed here. A note, not a row: the PASS / FAIL count is unchanged. Never stops the digest.
    try: ol = [(ops.get_blob_client(b.name).download_blob().readall().decode('utf-8', 'replace').strip().splitlines() or [''])[0][:300] for b in sorted(ops.list_blobs(name_starts_with=f'digest/lines/{NIGHT}/'), key=lambda x: x.name)]
    except Exception as e: ol = [f'not read (flag): {repr(e)[:120]}']
    st['order_lines'] = ol
    lines += [f'- **Order lines** (ops/digest/lines/{NIGHT}/): ' + ('none tonight' if not ol else '')] + [f'  - {x}' for x in ol]
    # OPS-06 B5 (CEO 2026-11-07): the standing list is no longer printed. Only a ruling added or superseded since the night before (tonight's standing
    # list against the one the previous digest carried) prints, under "New ruling"; nothing prints on a night without one. The list stays in digest.json.
    if L:
        pn = (datetime.date.fromisoformat(NIGHT) - datetime.timedelta(days=1)).isoformat()
        pv = ((get_json(ops, f'{pn}/digest.json') or {}).get('state') or {}).get('rulings')
        if pv is None: st['rulings_new'] = None; st['rulings_note'] = f'no ruling list in the {pn} digest: nothing compared'
        else:
            was = {x['id']: x['line'] for x in pv}; now_ = {x['id']: x['line'] for x in st['rulings']}
            st['rulings_new'] = [{'id': i, 'line': now_[i], 'change': 'added'} for i in now_ if i not in was] + [{'id': i, 'line': was[i], 'change': 'superseded'} for i in was if i not in now_]
        if st.get('rulings_new'):
            lines += ['- **New ruling:**'] + [f"  - {x['id']} · {x['change']} · {x['line']}" for x in st['rulings_new']]
    return st, lines

def daily():
    akey = az('storage', 'account', 'keys', 'list', '-n', APEX_SA, '-g', 'allooloo-cmkg-shared', '--query', '[0].value', '-o', 'tsv', raw=True)
    ops = client(APEX_SA, akey, OPS); sw = client(APEX_SA, akey, SWEEPS)
    prev_night = (datetime.date.fromisoformat(NIGHT) - datetime.timedelta(days=1)).isoformat()
    prev = {r['agent']: r for r in ((get_json(ops, f'{prev_night}/digest.json') or {}).get('rows') or [])}
    rows = []; spend_lines = []; RAN = {}; RAN_AT = {}; BF = []
    def row(agent, group, as_of, verdict, n, flags, hands, node=None, ark=None):
        # ORDER-037 §3.4 (OPS-ALLOOLOO 2026-10-30): node and ark delta (objects written to the ark tonight) beside the row delta against the night before
        p = prev.get(agent, {}).get('rows'); delta = (n - p) if isinstance(n, int) and isinstance(p, int) else None
        rows.append({'agent': agent, 'group': group, 'node': node, 'as_of': as_of, 'verdict': verdict, 'rows': n, 'delta': delta, 'ark_delta': ark, 'flags': flags, 'hand_items': hands})
    for cc, reg in NODES:
        sa = f'allooloocmkg{cc}pond'
        try:
            k = az('storage', 'account', 'keys', 'list', '-n', sa, '-g', f'allooloo-cmkg-{reg}', '--query', '[0].value', '-o', 'tsv', raw=True); c = client(sa, k, 'pond')
            d = get_json(c, f'sweeps/{NIGHT}/{cc}/done.json'); f = None if d else get_json(c, f'sweeps/{NIGHT}/{cc}/failed.json'); s = None if (d or f) else get_json(c, f'sweeps/{NIGHT}/{cc}/skipped.json')
        except Exception as e: d = f = s = c = None; log(f'{cc}: store not read', repr(e)[:160])
        try:   # BACKFILL-01 B-6 (DAY ORDER 7): the backfill counts beside the live rows, never in them (backfill rows are not digest counts)
            if c is None: raise RuntimeError('store not read')
            bf = get_json(c, 'backfill/facts.json'); bmk = get_json(c, f'sweeps-backfill/{NIGHT}/{cc}/done.json'); bfl = None if bmk else get_json(c, f'sweeps-backfill/{NIGHT}/{cc}/failed.json')
            # ZONES-03 standing line (2026-10-27): manifests held and the ark objects of the market's newest backfill run (its own done marker)
            mans = sum(1 for b in c.list_blobs(name_starts_with='backfill/') if re.match(r'backfill/\d{4}/manifest\.json$', b.name))
            lastm = sorted(b.name for b in c.list_blobs(name_starts_with='sweeps-backfill/') if b.name.endswith(f'/{cc}/done.json'))
            lm = get_json(c, lastm[-1]) if lastm else None; ak = re.search(r'ark: (\d+) objects', clean((lm or {}).get('tail') or ''))
            errl = [l.strip() for l in clean(((bfl or {}).get('tail') or '') + '\n' + ((bfl or {}).get('error') or '')).splitlines() if re.match(r'\s*[\w.]+(Error|Exception)\b', l) or l.strip().startswith('FAIL')]
            BF.append({'fail_reason': (errl[-1][:110] if errl else None), 'manifests': mans, 'ark_objects_last_run': int(ak.group(1)) if ak else None, 'last_run_night': (lm or {}).get('night'),
                       'node': f'{cc}-cm-kg', 'year_in_progress': (bf or {}).get('year_in_progress'), 'years_done': sorted((bf or {}).get('years') or {}, reverse=True), 'rows': (bf or {}).get('rows'), 'docs': (bf or {}).get('documents'), 'depth': (bf or {}).get('history_from'),
                       'storage_bytes': (bf or {}).get('storage_bytes'), 'night': 'ran' if bmk else ('FAILED: ' + clean((bfl or {}).get('error') or (bfl or {}).get('tail') or '')[-160:] if bfl else 'no run tonight')})
        except Exception: pass
        if d:
            fl = [f"records {d.get('records_delta', 0):+d} · events {d.get('events_delta', 0):+d}"]; a = d.get('ark') or {}
            if d.get('held'): fl.append('HELD: ' + clean(d.get('held_flag') or '')[:200])
            if a.get('error') or (a.get('enabled') and not a.get('objects')): fl.append('ARK FAILED')
            elif not a.get('enabled'): fl.append('ark not enabled')
            hands = (["publish on the CEO's go (publish_held.py)"] if d.get('held') else []) + hand_items(d)   # OPS-06 B6: the go line (was: "door held: the machine half explains the drop, the CEO go publishes")
            row(f'{cc}-cm-kg', 'node', d.get('as_of'), 'HELD' if d.get('held') else ('FAIL' if 'ARK FAILED' in fl else 'PASS'), d.get('records'), fl, hands, node=cc, ark=len(a.get('objects') or []) if a.get('enabled') else None); spend_lines += d.get('spend_lines') or []
            RAN[f'cmkg-{cc}-rail'] = d.get('image'); RAN_AT[f'cmkg-{cc}-rail'] = d.get('started_utc')   # DIGEST-CAP-01 addendum: the tag the job ran tonight, from its own marker (+ when it started, Line 0)
        elif f: row(f'{cc}-cm-kg', 'node', None, 'FAIL', None, [clean(f.get('error') or 'failed')[:200]], [], node=cc)
        else: row(f'{cc}-cm-kg', 'node', None, 'NOT LANDED', None, ['skipped: ' + clean(s.get('why') or '') if s else 'no marker for this night'], [], node=cc)
    a = get_json(sw, f'{NIGHT}/apex-done.json')
    if a:
        landed = a.get('landed') or []; ok = len(landed) == len(NODES) and not a.get('failed') and 'FAILED' not in (a.get('close_line') or '')
        row('apex', 'apex', a.get('market_date'), 'PASS' if ok else 'FAIL', a.get('records'), [f"{len(landed)} of {len(NODES)} landed", clean(a.get('close_line'))[:220]], [], node='apex', ark=len((a.get('ark') or {}).get('objects') or []) if (a.get('ark') or {}).get('enabled') else None)
    else: row('apex', 'apex', None, 'NOT LANDED', None, ['no apex-done.json for this night'], [])
    sas = os.environ.get('ISSUERWIRE_POND_SAS', '')
    iw = ContainerClient.from_container_url(f'https://stgamnfrc.blob.core.windows.net/pond?{sas.lstrip("?")}') if sas else None
    if not iw and DRY_DIR:   # laptop test only: the signed-in az reads the GSC-tenant pond with its own key (never on the job)
        try: iw = client('stgamnfrc', az('storage', 'account', 'keys', 'list', '-n', 'stgamnfrc', '--subscription', '9e406344-81a4-4624-98de-a9c642a75d69', '--query', '[0].value', '-o', 'tsv', raw=True), 'pond')
        except Exception as e: log('issuerwire pond not read on the laptop:', repr(e)[:160])
    for job, field in IW:
        d = get_json(iw, f'ops/{NIGHT}/{job}/done.json') if iw else None; f = None if d or not iw else get_json(iw, f'ops/{NIGHT}/{job}/failed.json')
        if d:
            v = d.get('verdict') or ('FAIL' if 'FAIL' in (d.get('count_check'), d.get('signature_check')) else 'PASS')
            fl = [f'{k} {d[k]}' for k in ('count_check', 'signature_check', 'refused', 'window_short') if k in d and d[k] not in (None, False, 0)]
            if job == 'stores':   # NIGHTLY-02 (CEO 2026-11-01): a drop to under half the prior night's is a FAIL unless the agent names its cause
                n0, p0 = d.get(field), prev.get('issuerwire-stores', {}).get('rows')
                if isinstance(n0, int) and isinstance(p0, int) and p0 >= 500 and n0 < p0 / 2:
                    if d.get('cause'): fl.append(f'drop {p0} -> {n0}: {clean(d["cause"])[:200]}')
                    else: v = 'FAIL'; fl.append(f'drop {p0} -> {n0} with no cause named by the agent')
            row(f'issuerwire-{job}', 'issuerwire', (d.get('finished_utc') or d.get('date') or '')[:10], v, d.get(field), fl, hand_items(d)); spend_lines += d.get('spend_lines') or []
        elif f: row(f'issuerwire-{job}', 'issuerwire', None, 'FAIL', None, [clean(f.get('error') or 'failed')[:200]], [])
        else: row(f'issuerwire-{job}', 'issuerwire', None, 'NOT LANDED', None, ['no marker for this night' if iw else 'issuerwire-pond-sas not set (flag)'], [])
    # ECO-01 (2026-10-23): the weekly eco-refresh agent (Sunday 05:00 UTC) writes its row to ops/digest/rows/<date>/eco-refresh.json; shown on the night it ran
    # a same-day re-run writes eco-refresh-<n>.json beside the day's row (2026-10-24): the night shows its latest run
    names = sorted((b.name for b in ops.list_blobs(name_starts_with=f'digest/rows/{NIGHT}/eco-refresh')), key=lambda x: int(re.search(r'-(\d+)\.json$', x).group(1)) if re.search(r'-(\d+)\.json$', x) else 1)
    e = get_json(ops, names[-1]) if names else None
    if e: row('eco-refresh', 'eco', NIGHT, e.get('verdict'), e.get('pages_read'), [f"fields flagged {e.get('fields_flagged')} · pages failed {e.get('pages_failed')} · markets {', '.join(e.get('markets_touched') or []) or 'none'}"], ['flagged fields go to the hunter: re-read, sourced or blank'] if e.get('fields_flagged') else [])
    # ECO-OPS-01 (2026-10-28): the nightly rebuild of the SM-ECO-10060 set writes digest/rows/<night>/eco-ops.json (a same-night re-run lands beside as eco-ops-<n>.json)
    names = sorted((b.name for b in ops.list_blobs(name_starts_with=f'digest/rows/{NIGHT}/eco-ops')), key=lambda x: int(re.search(r'-(\d+)\.json$', x).group(1)) if re.search(r'-(\d+)\.json$', x) else 1)
    e = get_json(ops, names[-1]) if names else None
    if e: row('eco-ops', 'eco', NIGHT, e.get('verdict'), e.get('hosts_changed'), (e.get('flags') or []) + ([] if e.get('rolled') else ['not rolled tonight']), e.get('hand_items') or [])
    else: row('eco-ops', 'eco', None, 'NOT LANDED', None, ['no eco-ops row for this night'], [])
    # RCO-CHAIN (2026-10-30, RCO build memo v1.0 §7): the RCO line is the rco-chain agent's row, digest/rows/<night>/rco-chain[-n].json (the night's latest).
    # "RCO · receipts today · total · chain OK/FAIL · anchored yes/no · writers seen". No row = FAIL "RCO: no readout" — silence is a FAIL, never a blank.
    # (Was: the office laptop readout C:\MATTHEWKEDDY\RCO\READOUT\latest.json — retired with the laptop task RCO-readout-nightly.)
    st = {}   # Line 0 (DAY ORDER 6): defined before the read, so the capacity block's ledger figure never falls to None when the read fails
    rco_row = None
    try:
        names = sorted((b.name for b in ops.list_blobs(name_starts_with=f'digest/rows/{NIGHT}/rco-chain')), key=lambda x: int(re.search(r'-(\d+)\.json$', x).group(1)) if re.search(r'-(\d+)\.json$', x) else 1)
        e = rco_row = get_json(ops, names[-1]) if names else None
        if e: row('rco-chain', 'rco', e.get('day'), e.get('verdict'), e.get('receipts_day'), [e.get('line')] + (e.get('flags') or []), e.get('hand_items') or [])
        else: row('rco-chain', 'rco', None, 'FAIL', None, ['RCO: no readout'], [])
        st = {'ledger': {'pending': 0}}
    except Exception as ex: row('rco-chain', 'rco', None, 'FAIL', None, ['RCO: no readout (' + repr(ex)[:100] + ')'], [])
    # OPS-ALLOOLOO step 1 + 4 (2026-10-30): rco-export — the door's nightly export (cron 30 5 * * * UTC) of the full receipts table and each key's Register slice to
    # s3://rco-receipts-copy, read from the door's own /health.json; the AWS copy status beside it: last put and the count check. The credential is put-only (read,
    # list and head refused by design), so the landing proof is the PUT's 200 + version id the door and rco-chain recorded, never a read-back.
    try:
        import requests
        h = requests.get('https://rco-records.ai/health.json', headers={'User-Agent': 'Allooloo digest (OPS-ALLOOLOO)'}, timeout=30).json().get('export') or {}
        last = h.get('last') or {}; anc = [s for s in (((rco_row or {}).get('anchor') or {}).get('spots') or []) if str(s.get('spot', '')).startswith('s3://')]
        ok = bool(h.get('armed')) and last.get('day') == NIGHT and last.get('status') == 200
        fl = [f"bucket {h.get('bucket')} ({h.get('region')}) · armed {h.get('armed')} · cron {h.get('cron')} · last put {last.get('day')} status {last.get('status')} at {str(last.get('at'))[:16]}Z",
              'anchor copy ' + (f"{anc[0].get('spot')} status {anc[0].get('status')}" + (f" ({anc[0].get('error')[:80]})" if anc[0].get('error') else '') if anc else 'not in the rco-chain row'),
              'count check: PUT 200 + version id (put-only credential; read-back refused by design)']
        row('rco-export', 'rco', last.get('day'), 'PASS' if ok else 'FAIL', None, fl, [] if ok else ['rco-export: the door export did not put tonight — read rco-records.ai/health.json'])
    except Exception as ex: row('rco-export', 'rco', None, 'NOT LANDED', None, ['door /health.json not read: ' + repr(ex)[:100]], [])
    # TMKT-04 (2026-11-02): tm-verify — the apex rail's re-fetch of every document a target market statement names; the drift count on the row
    try:
        tv = get_json(ops, 'tm-verify/latest.json')
        if tv: row('tm-verify', 'tm', tv.get('day'), 'PASS' if tv.get('day') == NIGHT else 'NOT LANDED', tv.get('drifted'), [f"{tv.get('statements')} statements · {tv.get('documents')} documents re-fetched · {tv.get('drifted')} drifted · {tv.get('drift_records_written')} drift records written (beside the statements; nothing removed)"], [])
        else: row('tm-verify', 'tm', None, 'NOT LANDED', None, ['ops/tm-verify/latest.json not written yet'], [])
    except Exception as ex: row('tm-verify', 'tm', None, 'NOT LANDED', None, ['ops/tm-verify/latest.json not read: ' + repr(ex)[:100]], [])
    # OPS-ALLOOLOO step 3 (2026-10-30): the Book's agent (book-of-markets, weekly) writes digest/rows/<night>/book-of-markets[-n].json; the row shows its latest
    # run of the last seven nights with its age — weekly, so a night without a run is not a FAIL; no row in seven nights is NOT LANDED.
    try:
        bk = None
        for i in range(7):
            n_ = (datetime.date.fromisoformat(NIGHT) - datetime.timedelta(days=i)).isoformat()
            nm = sorted((b.name for b in ops.list_blobs(name_starts_with=f'digest/rows/{n_}/book-of-markets')), key=lambda x: int(re.search(r'-(\d+)\.json$', x).group(1)) if re.search(r'-(\d+)\.json$', x) else 1)
            if nm: bk = (n_, get_json(ops, nm[-1])); break
        if bk and bk[1]:
            b = bk[1]; age = (datetime.date.fromisoformat(NIGHT) - datetime.date.fromisoformat(bk[0])).days
            row('book-of-markets', 'book', bk[0], b.get('verdict'), b.get('sections_read'), [f"markets {b.get('markets')} · sections read {b.get('sections_read')} · fields changed {b.get('fields_changed')} · not-found {b.get('not_found')} · FAIL {b.get('fail')}" + (f' · ran {age} night(s) ago (weekly)' if age else ' · ran tonight')] + (b.get('flags') or []), b.get('hand_items') or [])
        else: row('book-of-markets', 'book', None, 'NOT LANDED', None, ['no book-of-markets row in the last seven nights'], [])
    except Exception as ex: row('book-of-markets', 'book', None, 'NOT LANDED', None, ['book row not read: ' + repr(ex)[:100]], [])
    # ORDER-037 §3.6 (2026-10-30): the mail step of the night before — the Logic App's runs read by this job's identity (Reader on the workflow). A digest whose
    # mail did not send carries a "mail FAIL <date>" row the next night; the digest file itself is already in the pond and the ark.
    try:
        pn = prev_night; wf = os.environ.get('DIGEST_LOGIC_APP', f'/subscriptions/{SUB}/resourceGroups/allooloo-cmkg-shared/providers/Microsoft.Logic/workflows/allooloo-ops-digest')
        runs = az('rest', '--method', 'get', '--url', f"https://management.azure.com{wf}/runs?api-version=2016-06-01&$filter=startTime ge {pn}T14:00:00Z and startTime lt {NIGHT}T14:00:00Z")
        st_ = [r['properties']['status'] for r in (runs or {}).get('value') or []]
        if 'Succeeded' in st_: row('digest-mail', 'digest', pn, 'PASS', st_.count('Succeeded'), [f'mail of {pn}: {len(st_)} run(s) · ' + ' '.join(st_)], [])
        else: row('digest-mail', 'digest', pn, 'FAIL', 0, [f'mail FAIL {pn}' + (f" ({' '.join(st_)})" if st_ else ' (no Logic App run)')], ['read the Logic App allooloo-ops-digest run history'])
    except Exception as ex: row('digest-mail', 'digest', prev_night, 'NOT LANDED', None, ['mail status not read: ' + repr(ex)[:120]], [])
    # X402-A-01 (2026-10-24): settlement counts on the Allooloo doors (counts only, never amounts)
    try:
        import requests
        xs = requests.get('https://allooloo.ai/x402/settled.json', headers={'User-Agent': 'Allooloo digest (X402-A-01)'}, timeout=30)
        xj = xs.json() if xs.status_code == 200 else None
        if xj: row('x402-settlements', 'x402', NIGHT, 'PASS', (xj.get('by_day') or {}).get(NIGHT, 0), [f"settled total {xj.get('settled', 0)} · free reads {(xj.get('free_by_day') or {}).get(NIGHT, 0)} · offers asked for {(xj.get('offers_by_day') or {}).get(NIGHT, 0)} · doors {len(xj.get('by_door') or {})} · no rationing (CEO ruling 2026-10-24): every read free for every agent; the offer only when asked; paid reads carry the settlement on the receipt"], [])
        else: row('x402-settlements', 'x402', None, 'NOT LANDED', None, [f'settlement counts answered {xs.status_code}'], [])
    except Exception as e: row('x402-settlements', 'x402', None, 'NOT LANDED', None, ['settlement counts not read: ' + repr(e)[:120]], [])
    # OPS-06 B2 (CEO 2026-11-07): one row per get_ door. Each: the page and the door call answer 200 on the wire; the answer's signature verifies
    # (Ed25519 against the published keyring; the Target Market statement through the door's own verify_target_market); the receipt it names verifies
    # on mcp.rco-records.ai and was cleared in this run (fresh). PASS only when all three hold. Five reads a night, one receipt each.
    for r_ in door_rows(): row(*r_)
    tav = None
    try:
        import requests
        r = requests.get('https://api.tavily.com/usage', headers={'Authorization': 'Bearer ' + os.environ.get('TAVILY_API_KEY', '')}, timeout=30)
        j = (r.json() if r.status_code == 200 else {}).get('account', {}); tav = {'plan_usage': j.get('plan_usage'), 'plan_limit': j.get('plan_limit'), 'paygo_usage': j.get('paygo_usage'), 'paygo_limit': j.get('paygo_limit'), 'read_at': T0.isoformat()}
    except Exception as e: log('Tavily meter not read:', repr(e)[:160])
    labs = spend_of(spend_lines)
    # DIGEST-CAP-01 (DAY ORDER 5, 2026-10-24): the capacity block — the limits read every morning, not found mid-chain.
    # Live tonight: doors answering (list_nodes on the resolver, then each node's public door /mcp.json), the Tavily balance left, lab $ this night, the
    # ledger backlog (RCO receipts written but not yet in the Confidential Ledger). As provisioned (ARM, which this job cannot read): environments against
    # the subscription limit, regions in use, door apps, jobs, stores — from ops/capacity/latest.json (capacity_snapshot.py), with the date it was read.
    cap = {}
    try:
        import requests
        ln = requests.post('https://mcp.getissuer.ai/mcp', json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'list_nodes', 'arguments': {}}}, headers={'accept': 'application/json', 'User-Agent': 'Allooloo digest (DIGEST-CAP-01)'}, timeout=30).json()
        nl = [n for n in ln['result']['structuredContent']['nodes'] if n.get('live')]; up = 0
        for n in nl:
            d = (n.get('regional_door') or n.get('door') or '').rstrip('/')
            d = d[:-4] if d.endswith('/mcp') else d
            try: up += requests.get(d + '/mcp.json', headers={'User-Agent': 'Allooloo digest (DIGEST-CAP-01)'}, timeout=20).status_code == 200
            except Exception: pass
        cap['doors'] = {'live_nodes': len(nl), 'answering': up}
        try:   # DAY ORDER 5: the two market counts of record — getissuer's live nodes and Issuerwire's markets (shown after two green nights; seeded apart)
            iwf = requests.get('https://issuerwire.ai/facts.json', headers={'User-Agent': 'Allooloo digest (DIGEST-CAP-01)'}, timeout=30).json()
            cap['markets'] = {'getissuer_nodes_live': len(nl), 'issuerwire_shown': iwf.get('markets_count', len(iwf.get('markets') or [])), 'issuerwire_seeded_not_shown': len(iwf.get('seeded_not_shown') or [])}
        except Exception as e: cap['markets'] = {'getissuer_nodes_live': len(nl), 'error': repr(e)[:80]}
    except Exception as e: cap['doors'] = {'error': repr(e)[:120]}
    if tav and tav.get('plan_limit') is not None:
        cap['tavily_left'] = int(max((tav.get('plan_limit') or 0) - (tav.get('plan_usage') or 0), 0) + ((tav.get('paygo_limit') or 0) - (tav.get('paygo_usage') or 0) if tav.get('paygo_limit') else 0))   # DIGEST-CAP-01: plan left (never below 0; usage past the plan is the pay-as-you-go use) + pay-as-you-go left, an integer (the meter returns 400000.0)
    cap['lab_usd_night'] = round(sum(v['usd'] for v in labs.values()), 2)
    cap['ledger_backlog'] = (st.get('ledger') or {}).get('pending') if st else 'not read (rco-receipts row)'   # Line 0 / ENUM-01 row 2 (DAY ORDER 6): st is the rco read above
    try: cap['provisioned'] = get_json(ops, 'capacity/latest.json')
    except Exception as e: cap['provisioned'] = None
    # DIGEST-CAP-01 addendum (2026-10-25): every cmkg-sweep job's tag against the fleet tag of record (this job's own IMAGE_TAG — every fleet move carries the
    # digest jobs); configured = the job definition (capacity snapshot, ARM), ran = tonight's marker. Any mismatch is a DRIFT row. Read from the jobs, never typed.
    FLEET = ((cap.get('provisioned') or {}).get('jobs') or {}).get('fleet_tag') or os.environ.get('FLEET_TAG') or IMAGE_TAG;   # FIX-01 drift (2026-11-12): the fleet tag is read from what runs (the capacity snapshot); the typed setting is the fallback
    #   # SITE-04 (2026-10-28): the fleet tag of record by env when the digest runs ahead of the node fleet
    tags = (((cap.get('provisioned') or {}).get('jobs') or {}).get('tags') or {}); cap['fleet_tag'] = FLEET; cap['job_tags'] = []
    for jn in sorted(set(k for k, v in tags.items() if v.get('repo') == 'cmkg-sweep') | set(RAN)):
        cfg = (tags.get(jn) or {}).get('tag'); ran = RAN.get(jn); mod = (tags.get(jn) or {}).get('modified'); at = RAN_AT.get(jn)
        # Line 0 (DAY ORDER 6, 2026-10-25): a night run on an older tag is DRIFT only if the job already named the fleet tag when it started. A job moved to the
        # fleet tag after tonight's run (definition modified after the run started) is not drift: it is 'moved after run', and its next run is on the fleet tag.
        moved_after = bool(ran and ran != FLEET and cfg == FLEET and mod and at and str(mod)[:19] > str(at)[:19])
        cap['job_tags'].append({'job': jn, 'configured': cfg, 'ran_tonight': ran, 'fleet': FLEET, 'moved_after_run': moved_after})
        bad = [x for x in (('configured', cfg), ('ran tonight', None if moved_after else ran)) if x[1] and x[1] != FLEET]
        if bad: row(jn, 'drift', NIGHT, 'DRIFT', None, [' · '.join(f'{k} {v}' for k, v in bad) + f' · fleet {FLEET}'], ['move the job to the fleet tag (provision_jobs.py upgrade)'])
    # ZONES-03 standing line (2026-10-27): backfill — markets closed (ledger complete) with years, manifests and ark objects; the next market waiting; FAILs named
    bf_line = 'Backfill · not read (flag)'
    try:
        POLF = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backfill', 'policy.json'), encoding='utf-8'))
        codes = [cc for cc, _ in NODES]; order = [cc for cc in POLF['order'] if cc in codes and (POLF.get('markets') or POLF).get(cc, {}).get('adapter') != 'none']
        led = client(APEX_SA, akey, 'backfill-order'); bfx = {x['node'][:2]: x for x in BF}; closed = []; nxt = None
        for cc in order:
            e = get_json(led, f'{cc}.json') or {}
            if e.get('complete'):
                x = bfx.get(cc) or {}; ys = sorted(int(y) for y in (x.get('years_done') or []))
                closed.append(f"{cc} — years {ys[0]}–{ys[-1] if ys else ''} ({len(ys)}) · {x.get('manifests', '—')} manifests · ark {x.get('ark_objects_last_run', '—')} objects (run {x.get('last_run_night') or '—'})" if ys else f"{cc} — years not read")
            elif nxt is None: lf = e.get('left'); nxt = (f"{cc} (to do: {' '.join(str(y) for y in lf) if isinstance(lf, list) else lf})" if e else f'{cc} (no ledger entry yet)')
        fails = [f"{x['node']}: {x.get('fail_reason') or 'failed (no error line in its marker)'}" for x in BF if str(x.get('night') or '').startswith('FAILED')]
        bf_line = f"Backfill · closed: {' ; '.join(closed) or 'none'} · next waiting: {nxt or 'none (every market complete)'} · FAIL: {' ; '.join(fails) if fails else 'none'}"
    except Exception as e: bf_line = f'Backfill · not read (flag): {repr(e)[:120]}'
    # TRAFFIC-RETIRE (CEO 2026-11-07): the traffic line is dropped from the nightly digest for good; cmkg-traffic-nightly is disarmed (cron parked, job and its
    # last read ops/traffic/latest.json kept for rollback). Allooloo traffic is read on demand only. (Was: SITE-04 line from ops/traffic/latest.json, OPS-06 freshness gate.)
    tr_line = None; tr_note = 'retired 2026-11-07: Allooloo traffic is read on demand only'
    try: ST, ST_LINES = state_block(ops, rows, cap)   # MORNING-01: the STATE block (before the sort; it reads tonight's rows)
    except Exception as e: ST, ST_LINES = {'error': repr(e)[:200]}, ['## STATE', '', f'STATE not generated (flag): {repr(e)[:200]}']
    # ORDER-037 §3.4 (OPS-ALLOOLOO 2026-10-30): FAIL rows sort to the top under the header (FAIL · HELD · DRIFT), then not landed, then PASS — stable within each
    rank = lambda r: 0 if r['verdict'] in ('FAIL', 'HELD', 'DRIFT') else (1 if r['verdict'] == 'NOT LANDED' else 2)
    rows.sort(key=rank)
    # OPS-06 B1 (CEO 2026-11-07): HELD counts on its own and is not a FAIL
    n_pass = sum(1 for r in rows if r['verdict'] == 'PASS'); n_fail = sum(1 for r in rows if r['verdict'] == 'FAIL'); n_held = sum(1 for r in rows if r['verdict'] == 'HELD')
    n_drift = sum(1 for r in rows if r['verdict'] == 'DRIFT'); n_nl = sum(1 for r in rows if r['verdict'] == 'NOT LANDED')
    na = [r['as_of'] for r in rows if r['group'] == 'node' and r['as_of']]; nodes_asof = max(set(na), key=na.count) if na else '—'   # the as_of most nodes landed with
    iw_asof = next((r['as_of'] for r in rows if r['agent'] == 'issuerwire-close' and r['as_of']), '—')
    # OPS-06 B1: the CEO's subject line; a NOT LANDED or DRIFT count is appended only on a night that has one (so neither is hidden); SUBJECT_PREFIX for a check send
    subject = (os.environ.get('SUBJECT_PREFIX', '').strip() + ' ').lstrip() + f'Allooloo nightly · {NIGHT} · {n_pass} PASS · {n_fail} FAIL · {n_held} HELD · nodes {nodes_asof} · issuerwire {iw_asof}' \
              + (f' · {n_nl} NOT LANDED' if n_nl else '') + (f' · {n_drift} DRIFT' if n_drift else '')
    dj = {'night': NIGHT, 'subject': subject, 'pass': n_pass, 'fail': n_fail, 'held': n_held, 'not_landed': n_nl, 'estate_traffic_note': tr_note, 'drift': n_drift, 'nodes_as_of': nodes_asof, 'issuerwire_as_of': iw_asof, 'rows': rows, 'spend_by_lab': labs, 'spend_lines': [clean(l) for l in spend_lines],
          'tavily_meter': tav, 'capacity': cap, 'backfill': BF, 'backfill_line': bf_line, 'estate_traffic_line': tr_line, 'execution': EXEC, 'image': IMAGE_TAG, 'written_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'state': ST, 'note': 'OPS-06: FAIL counts FAIL only; HELD counted on its own; NOT LANDED is counted apart (schedule or no marker); DRIFT apart'}
    fmt = lambda v: '—' if v is None else (f'{v:,}' if isinstance(v, int) else str(v))
    sgn = lambda v: '—' if v is None else (f'{v:+,}' if v else '0')
    rcell = lambda r: fmt(r['rows']) + (f" (Δ{sgn(r['delta'])})" if r['delta'] is not None else '')
    table = ['| agent | node | as_of | verdict | rows | ark delta | flags | hand items |', '|---|---|---|---|---|---|---|---|'] + [f"| {r['agent']} | {r.get('node') or '—'} | {r['as_of'] or '—'} | {r['verdict']} | {rcell(r)} | {fmt(r.get('ark_delta'))} | {' · '.join(x for x in r['flags'] if x) or '—'} | {' · '.join(r['hand_items']) or '—'} |" for r in rows]
    # OPS-06 B8 (CEO 2026-11-07): non-zero spend only; when everything is zero, one line "Spend · $0 tonight"
    nz = {k: v for k, v in labs.items() if round(v['usd'], 2) != 0}
    spend_t = (['| lab | lines | usd |', '|---|---|---|'] + [f'| {k} | {v["lines"]} | ${v["usd"]:.2f} |' for k, v in sorted(nz.items())]) if nz else ['Spend · $0 tonight']
    spend_line = ('Spend · ' + ' · '.join(f'{k} ${v["usd"]:.2f}' for k, v in sorted(nz.items()))) if nz else 'Spend · $0 tonight'
    spend_nz = [l for l in dj['spend_lines'] if any(float(m) for m in re.findall(r'\$([\d.]+)', l) if m.replace('.', '', 1).isdigit())]
    meter = f"Tavily meter: plan {tav['plan_usage']:,} of {tav['plan_limit']:,} · pay-as-you-go {tav.get('paygo_usage')} of {tav.get('paygo_limit')} (GET /usage, account-wide, read {T0.strftime('%H:%M')}Z)" if tav and tav.get('plan_usage') is not None and tav.get('plan_limit') else 'Tavily meter: not read (flag)'
    private = f'Private: allooloocmkgapex/ops/{NIGHT}/'
    pv = cap.get('provisioned') or {}; ev = pv.get('environments') or {}
    mk = cap.get('markets') or {}
    cap_line0 = f"Markets · getissuer {mk.get('getissuer_nodes_live', '—')} nodes live · Issuerwire {mk.get('issuerwire_shown', '—')} shown + {mk.get('issuerwire_seeded_not_shown', '—')} seeded (shown after two green nights)"
    cap_line = (f"Capacity · doors answering {(cap.get('doors') or {}).get('answering', '—')} of {(cap.get('doors') or {}).get('live_nodes', '—')} live · "
                f"jobs {(pv.get('jobs') or {}).get('count', '—')} · door apps {(pv.get('doors') or {}).get('apps', '—')} · environments {ev.get('used', '—')} of {ev.get('limit', '—')} ({ev.get('free', '—')} free) · "
                f"regions in use {len(ev.get('regions') or [])} environments / {len((pv.get('stores') or {}).get('regions') or [])} stores · Tavily left {fmt(cap.get('tavily_left'))} · lab ${cap.get('lab_usd_night', 0):.2f} tonight · "
                f"ledger backlog {cap.get('ledger_backlog', '—')} · provisioned as read {str(pv.get('read_utc', 'not read'))[:10]}")   # Line 0 (DAY ORDER 6): the Tavily figure prints through fmt (— when the meter was not read), so the line never stops the digest
    md = '\n'.join([f'# DIGEST · Allooloo nightly · {NIGHT}', '', subject, '', *ST_LINES, '', f'written by {EXEC} (image {IMAGE_TAG}) · private ops store, never public', '', '## Agents', '', *table, '', spend_line, '', meter, '', private, '',
                    '## Capacity', '', cap_line0, '', cap_line, '', *([tr_line, ''] if tr_line else []), f"Fleet tag of record {cap.get('fleet_tag')} · {len(cap.get('job_tags') or [])} jobs · {n_drift} DRIFT", '', '| job | configured | ran tonight | fleet |', '|---|---|---|---|', *[f"| {x['job']} | {x['configured'] or '—'} | {(x['ran_tonight'] or '—') + (' (moved to the fleet tag after this run)' if x.get('moved_after_run') else '')} | {x['fleet']} |" for x in (cap.get('job_tags') or [])], '', '## Backfill (Allooloo Datasets · BACKFILL-01)', '', bf_line, '', '| market | BACKFILL · year in progress | years done | rows | docs | depth (history_from) | storage | tonight |', '|---|---|---|---|---|---|---|---|', *[f"| {x['node']} | {x['year_in_progress'] or '—'} | {' '.join(x['years_done']) or '—'} | {fmt(x['rows'])} | {fmt(x['docs'])} | {x['depth'] or '—'} | {fmt(x['storage_bytes'])} | {x['night']} |" for x in BF], '', '## Spend per lab', '', *spend_t, '', *(['## Spend lines', '', '```', *spend_nz, '```', ''] if spend_nz else [])])
    n1 = put_beside(ops, f'{NIGHT}/DIGEST-{NIGHT}.md', md, 'text/markdown'); n2 = put_beside(ops, f'{NIGHT}/digest.json', json.dumps(dj, ensure_ascii=False, indent=1), 'application/json')
    # ORDER-037 §3.5 (OPS-ALLOOLOO 2026-10-30): the digest and its json copied to the apex ark (allooloo-ark-apex, Object Lock) by the ark-writer identity
    # (puts only; versioning keeps a re-run beside); count check = objects put with a version id against objects sent
    ark_line = 'Ark: not enabled (ARK_ENABLED unset)'
    if os.environ.get('ARK_ENABLED') == '1' and not DRY_DIR:
        sent = [(md.encode('utf-8'), f"apex/digest/{NIGHT}/{n1.split('/')[-1]}"), (json.dumps(dj, ensure_ascii=False, indent=1).encode('utf-8'), f"apex/digest/{NIGHT}/{n2.split('/')[-1]}")]; got = []
        try:
            import boto3, base64, hashlib
            s3 = boto3.client('s3', region_name=os.environ.get('ARK_REGION', 'us-east-1')); bk = os.environ.get('ARK_BUCKET', 'allooloo-ark-apex')
            for data, k in sent:
                r = s3.put_object(Bucket=bk, Key=k, Body=data, ContentMD5=base64.b64encode(hashlib.md5(data).digest()).decode())
                if r.get('VersionId'): got.append({'key': k, 'version_id': r['VersionId']})
            ark_line = f"Ark: s3://{bk}/apex/digest/{NIGHT}/ · {len(got)} of {len(sent)} put · count check {'PASS' if len(got) == len(sent) else 'FAIL'}"
        except Exception as ex: ark_line = f'Ark: FAILED ({repr(ex)[:120]}) · {len(got)} of {len(sent)} put · count check FAIL'
        put_beside(ops, f'{NIGHT}/digest-ark.json', json.dumps({'night': NIGHT, 'line': ark_line, 'objects': got, 'sent': len(sent)}, ensure_ascii=False, indent=1), 'application/json')
    log(ark_line)
    # ORDER-037 §3.6: subject = the header line; body = the digest as plain text in one monospace block; no attachments, no links but the private path
    import html as _h
    w = lambda s, n: (s if len(s) <= n else s[:n - 1] + '…').ljust(n)
    plain = [subject, '', *[l.replace('**', '').strip('*') for l in ST_LINES if l], '', w('agent', 26) + w('node', 6) + w('as_of', 12) + w('verdict', 11) + w('rows', 22) + w('ark', 7) + 'flags · hand items']
    plain += [w(r['agent'], 26) + w(r.get('node') or '—', 6) + w(str(r['as_of'] or '—'), 12) + w(r['verdict'], 11) + w(rcell(r), 22) + w(fmt(r.get('ark_delta')), 7) + (' · '.join(x for x in r['flags'] if x)[:(400 if not r['hand_items'] else 300)] + (' · ' + ' · '.join(r['hand_items']) if r['hand_items'] else '')) for r in rows]   # OPS-06: the hand items (the held go line) are never trimmed off
    plain += ['', spend_line, meter, private, ark_line, '', cap_line0, cap_line] + ([tr_line] if tr_line else []) + [bf_line]
    body = '<pre style="font:12px Consolas,Menlo,monospace">' + _h.escape('\n'.join(plain)) + '</pre>'
    n3 = put_beside(ops, f'mail/{NIGHT}.json', json.dumps({'to': os.environ.get('DIGEST_TO', 'developers@allooloo.ai'), 'subject': subject, 'html': body, 'text': '\n'.join(plain)}, ensure_ascii=False), 'application/json')
    log(subject, '->', n1, n2, n3); return 0

def week():
    pt, dst = pacific_now(T0)
    if not FORCE and not (pt.weekday() == 5 and pt.hour == 6): log(f'not 06:00 Saturday Pacific (now {pt:%a %H:%M} {"PDT" if dst else "PST"}) — nothing written'); return 0
    akey = az('storage', 'account', 'keys', 'list', '-n', APEX_SA, '-g', 'allooloo-cmkg-shared', '--query', '[0].value', '-o', 'tsv', raw=True)
    ops = client(APEX_SA, akey, OPS); sw = client(APEX_SA, akey, SWEEPS); day = pt.date()
    nights = [(day - datetime.timedelta(days=i)).isoformat() for i in range(7, 0, -1)]   # the seven nights ending Friday
    digs = {n: get_json(ops, f'{n}/digest.json') for n in nights}
    agents = []
    for n in nights:
        for r in (digs[n] or {}).get('rows') or []:
            if r['agent'] not in agents: agents.append(r['agent'])
    v = lambda n, a: next((r for r in ((digs[n] or {}).get('rows') or []) if r['agent'] == a), None)
    grid = ['| agent | ' + ' | '.join(n[5:] for n in nights) + ' |', '|---|' + '---|' * 7]
    fails = []; hands = []
    for a in agents:
        cells = []
        for i, n in enumerate(nights):
            r = v(n, a); cells.append('·' if not digs[n] else ((r or {}).get('verdict') or '—'))
            if r and r['verdict'] in ('FAIL', 'HELD'):
                cleared = next((m for m in nights[i + 1:] if (v(m, a) or {}).get('verdict') == 'PASS'), None)
                fails.append(f"- {n} · {a} · {r['verdict']} · {' · '.join(r['flags'])[:220]} · {'cleared ' + cleared if cleared else 'OPEN at week close'}")
            for h in (r or {}).get('hand_items') or []:
                if f'{a}: {h}' not in hands: hands.append(f'{a}: {h}')
        grid.append(f'| {a} | ' + ' | '.join(cells) + ' |')
    labs = {}
    for n in nights:
        for k, e in ((digs[n] or {}).get('spend_by_lab') or {}).items(): x = labs.setdefault(k, {'usd': 0.0, 'lines': 0}); x['usd'] = round(x['usd'] + e['usd'], 4); x['lines'] += e['lines']
    meters = [(digs[n] or {}).get('tavily_meter') for n in nights if (digs[n] or {}).get('tavily_meter')]
    apex = get_json(sw, f'{nights[-1]}/apex-done.json') or {}
    x_line = clean(apex.get('x_line_staged') or '') or '(no apex marker on the last night — no X line staged)'
    missing = [n for n in nights if not digs[n]]
    md = '\n'.join([f'# sweepREVIEW-WEEK · week ending {day.isoformat()} (Saturday 06:00 Pacific) · nights {nights[0]} → {nights[-1]}', '',
        '## Human half (the CEO fills)', '', '- Reviewed: ', '- X line posted (from @allooloo_ai): ', '- Spend approved: ', '- Zones: ', '- Deletions: ', '- Rules: ', '- Registry publishes: ', '',
        f'*(Machine half written by {EXEC}, image {IMAGE_TAG}, from the seven nightly digests in allooloocmkgapex/ops. "·" = no digest that night{": " + ", ".join(missing) if missing else ""}.)*', '',
        '## Seven nights per agent', '', *grid, '', '## Every FAIL and its fix', '', *(fails or ['- none']), '', '## Hand items', '', *([f'- {h}' for h in hands] or ['- none']), '',
        '## The week\'s spend', '', '| lab | lines | usd |', '|---|---|---|', *[f'| {k} | {e["lines"]} | ${e["usd"]:.2f} |' for k, e in sorted(labs.items())], '',
        (f"Tavily meter: plan {meters[0]['plan_usage']:,} → {meters[-1]['plan_usage']:,} of {meters[-1]['plan_limit']:,} over the week (account-wide)" if len(meters) >= 1 and meters[0].get('plan_usage') is not None and meters[-1].get('plan_limit') else 'Tavily meter: not read this week'), '',
        '## X line (STAGED — the CEO posts from @allooloo_ai, never the job)', '', '```', x_line, '```', ''])
    n1 = put_beside(ops, f'week/sweepREVIEW-WEEK-{day.isoformat()}.md', md, 'text/markdown'); n2 = put_beside(sw, f'{day.isoformat()}/sweepREVIEW-WEEK-{day.isoformat()}.md', md, 'text/markdown')
    log('sweepREVIEW-WEEK written ->', n1, n2); return 0

def main():
    log(f'ORDER-037 digest job: mode {MODE}, night {NIGHT}, image {IMAGE_TAG}, execution {EXEC}')
    if not DRY_DIR: subprocess.run(['az', 'login', '--identity', '-o', 'none'], check=True); subprocess.run(['az', 'account', 'set', '-s', SUB], check=True)
    acct = az('account', 'show', *(['--subscription', SUB] if DRY_DIR else []))
    if acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
    return week() if MODE == 'week' else daily()

if __name__ == '__main__':
    try: rc = main()
    except SystemExit as e: rc = e.code if isinstance(e.code, int) else 1; log('STOP', e)
    except Exception as e: rc = 1; log('FAILED', repr(e)[:400]); log(traceback.format_exc()[-2000:])
    try:
        key = az('storage', 'account', 'keys', 'list', '-n', APEX_SA, '-g', 'allooloo-cmkg-shared', '--query', '[0].value', '-o', 'tsv', raw=True)
        put_beside(client(APEX_SA, key, OPS), f'{NIGHT}/digest-job-{MODE}-{EXEC}.log', '\n'.join(LOG) + '\n', 'text/plain')
    except Exception: pass
    sys.exit(rc)
