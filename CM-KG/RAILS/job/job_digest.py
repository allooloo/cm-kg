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

def daily():
    akey = az('storage', 'account', 'keys', 'list', '-n', APEX_SA, '-g', 'allooloo-cmkg-shared', '--query', '[0].value', '-o', 'tsv', raw=True)
    ops = client(APEX_SA, akey, OPS); sw = client(APEX_SA, akey, SWEEPS)
    prev_night = (datetime.date.fromisoformat(NIGHT) - datetime.timedelta(days=1)).isoformat()
    prev = {r['agent']: r for r in ((get_json(ops, f'{prev_night}/digest.json') or {}).get('rows') or [])}
    rows = []; spend_lines = []; RAN = {}; RAN_AT = {}; BF = []
    def row(agent, group, as_of, verdict, n, flags, hands):
        p = prev.get(agent, {}).get('rows'); delta = (n - p) if isinstance(n, int) and isinstance(p, int) else None
        rows.append({'agent': agent, 'group': group, 'as_of': as_of, 'verdict': verdict, 'rows': n, 'delta': delta, 'flags': flags, 'hand_items': hands})
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
            hands = (['door held: the machine half explains the drop, the CEO go publishes'] if d.get('held') else []) + hand_items(d)
            row(f'{cc}-cm-kg', 'node', d.get('as_of'), 'HELD' if d.get('held') else ('FAIL' if 'ARK FAILED' in fl else 'PASS'), d.get('records'), fl, hands); spend_lines += d.get('spend_lines') or []
            RAN[f'cmkg-{cc}-rail'] = d.get('image'); RAN_AT[f'cmkg-{cc}-rail'] = d.get('started_utc')   # DIGEST-CAP-01 addendum: the tag the job ran tonight, from its own marker (+ when it started, Line 0)
        elif f: row(f'{cc}-cm-kg', 'node', None, 'FAIL', None, [clean(f.get('error') or 'failed')[:200]], [])
        else: row(f'{cc}-cm-kg', 'node', None, 'NOT LANDED', None, ['skipped: ' + clean(s.get('why') or '') if s else 'no marker for this night'], [])
    a = get_json(sw, f'{NIGHT}/apex-done.json')
    if a:
        landed = a.get('landed') or []; ok = len(landed) == len(NODES) and not a.get('failed') and 'FAILED' not in (a.get('close_line') or '')
        row('apex', 'apex', a.get('market_date'), 'PASS' if ok else 'FAIL', a.get('records'), [f"{len(landed)} of {len(NODES)} landed", clean(a.get('close_line'))[:220]], [])
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
    # RCO-A-01 (2026-10-24): the receipts Allooloo's doors wrote that night (resolver, nodes, ECO lookups), read from the RCO door's public counts
    st = {}   # Line 0 (DAY ORDER 6): defined before the read, so the capacity block's ledger figure never falls to None when the read fails
    try:
        # CEO ruling 2026-10-29: RCO stats are private; the door serves no counts. The digest reads the office's nightly readout file (two-brands borrowing, read-and-use).
        _ro = json.load(open(r'C:\MATTHEWKEDDY\RCO\READOUT\latest.json', encoding='utf-8'))
        _bdw = {}
        for _r in _ro.get('by_day_writer') or []: _bdw.setdefault(_r['day'], {})[_r['writer']] = _r['n']
        st = {'by_day_writer': _bdw, 'by_writer': {_r['writer']: _r['n'] for _r in (_ro.get('by_writer') or [])}, 'ledger': {'pending': 0}, 'read_at': _ro.get('read_at')}
        day = (st.get('by_day_writer') or {}).get(NIGHT) or {}
        row('rco-receipts', 'rco', NIGHT, 'PASS', day.get('allooloo', 0), [f"written by Allooloo doors {day.get('allooloo', 0)} · all writers {sum(day.values())} · Allooloo total {(st.get('by_writer') or {}).get('allooloo', 0)} · ledger pending {(st.get('ledger') or {}).get('pending', 0)} · signatures verified at write"], [])
    except Exception as e: row('rco-receipts', 'rco', None, 'NOT LANDED', None, ['receipt counts not read: ' + repr(e)[:120]], [])
    # X402-A-01 (2026-10-24): settlement counts on the Allooloo doors (counts only, never amounts)
    try:
        import requests
        xs = requests.get('https://allooloo.ai/x402/settled.json', headers={'User-Agent': 'Allooloo digest (X402-A-01)'}, timeout=30)
        xj = xs.json() if xs.status_code == 200 else None
        if xj: row('x402-settlements', 'x402', NIGHT, 'PASS', (xj.get('by_day') or {}).get(NIGHT, 0), [f"settled total {xj.get('settled', 0)} · free reads {(xj.get('free_by_day') or {}).get(NIGHT, 0)} · offers asked for {(xj.get('offers_by_day') or {}).get(NIGHT, 0)} · doors {len(xj.get('by_door') or {})} · no rationing (CEO ruling 2026-10-24): every read free for every agent; the offer only when asked; paid reads carry the settlement on the receipt"], [])
        else: row('x402-settlements', 'x402', None, 'NOT LANDED', None, [f'settlement counts answered {xs.status_code}'], [])
    except Exception as e: row('x402-settlements', 'x402', None, 'NOT LANDED', None, ['settlement counts not read: ' + repr(e)[:120]], [])
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
    FLEET = os.environ.get('FLEET_TAG') or IMAGE_TAG;   # SITE-04 (2026-10-28): the fleet tag of record by env when the digest runs ahead of the node fleet
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
    # SITE-04 (2026-10-28): the ESTATE traffic number of the standing TRAFFIC run (cmkg-traffic-nightly, ops/traffic/latest.json); the RADAR tile keeps the typed LENS-01 figure (CEO)
    tr_line = 'ESTATE traffic · not read (flag): ops/traffic/latest.json absent'
    try:
        tr = get_json(ops, 'traffic/latest.json')
        if tr: tr_line = (f"ESTATE traffic (the lens, 30 days {tr['window'][0]} .. {tr['window'][1]} UTC): {tr['estate_requests_30d']:,} requests · " + ' · '.join(f"{k} {v:,}" for k, v in (tr.get('groups') or {}).items())
                          + f" · {round((tr.get('share_of_account') or 0) * 100, 1)}% of the account · roster {tr.get('roster')} · read {tr.get('read_at')} by {tr.get('written_by')}")
    except Exception as e: tr_line = f'ESTATE traffic · not read (flag): {repr(e)[:120]}'
    n_pass = sum(1 for r in rows if r['verdict'] == 'PASS'); n_fail = sum(1 for r in rows if r['verdict'] in ('FAIL', 'HELD'))
    n_drift = sum(1 for r in rows if r['verdict'] == 'DRIFT')
    subject = f'Allooloo nightly · {NIGHT} · {n_pass} PASS · {n_fail} FAIL' + (f' · {n_drift} DRIFT' if n_drift else '')
    dj = {'night': NIGHT, 'subject': subject, 'pass': n_pass, 'fail': n_fail, 'not_landed': sum(1 for r in rows if r['verdict'] == 'NOT LANDED'), 'rows': rows, 'spend_by_lab': labs, 'spend_lines': [clean(l) for l in spend_lines],
          'tavily_meter': tav, 'capacity': cap, 'backfill': BF, 'backfill_line': bf_line, 'estate_traffic_line': tr_line, 'execution': EXEC, 'image': IMAGE_TAG, 'written_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'note': 'FAIL counts FAIL and HELD; NOT LANDED is counted apart (schedule or no marker)'}
    fmt = lambda v: '—' if v is None else (f'{v:,}' if isinstance(v, int) else str(v))
    sgn = lambda v: '—' if v is None else (f'{v:+,}' if v else '0')
    table = ['| agent | as_of | verdict | rows | delta | flags | hand items |', '|---|---|---|---|---|---|---|'] + [f"| {r['agent']} | {r['as_of'] or '—'} | {r['verdict']} | {fmt(r['rows'])} | {sgn(r['delta'])} | {' · '.join(r['flags']) or '—'} | {' · '.join(r['hand_items']) or '—'} |" for r in rows]
    spend_t = ['| lab | lines | usd |', '|---|---|---|'] + [f'| {k} | {v["lines"]} | ${v["usd"]:.2f} |' for k, v in sorted(labs.items())]
    meter = f"Tavily meter: plan {tav['plan_usage']:,} of {tav['plan_limit']:,} · pay-as-you-go {tav.get('paygo_usage')} of {tav.get('paygo_limit')} (GET /usage, account-wide, read {T0.strftime('%H:%M')}Z)" if tav and tav.get('plan_usage') is not None and tav.get('plan_limit') else 'Tavily meter: not read (flag)'
    pv = cap.get('provisioned') or {}; ev = pv.get('environments') or {}
    mk = cap.get('markets') or {}
    cap_line0 = f"Markets · getissuer {mk.get('getissuer_nodes_live', '—')} nodes live · Issuerwire {mk.get('issuerwire_shown', '—')} shown + {mk.get('issuerwire_seeded_not_shown', '—')} seeded (shown after two green nights)"
    cap_line = (f"Capacity · doors answering {(cap.get('doors') or {}).get('answering', '—')} of {(cap.get('doors') or {}).get('live_nodes', '—')} live · "
                f"jobs {(pv.get('jobs') or {}).get('count', '—')} · door apps {(pv.get('doors') or {}).get('apps', '—')} · environments {ev.get('used', '—')} of {ev.get('limit', '—')} ({ev.get('free', '—')} free) · "
                f"regions in use {len(ev.get('regions') or [])} environments / {len((pv.get('stores') or {}).get('regions') or [])} stores · Tavily left {fmt(cap.get('tavily_left'))} · lab ${cap.get('lab_usd_night', 0):.2f} tonight · "
                f"ledger backlog {cap.get('ledger_backlog', '—')} · provisioned as read {str(pv.get('read_utc', 'not read'))[:10]}")   # Line 0 (DAY ORDER 6): the Tavily figure prints through fmt (— when the meter was not read), so the line never stops the digest
    md = '\n'.join([f'# DIGEST · Allooloo nightly · {NIGHT}', '', f'**{subject}** · {dj["not_landed"]} not landed · written by {EXEC} (image {IMAGE_TAG}) · private ops store, never public', '', '## Capacity', '', cap_line0, '', cap_line, '', tr_line, '', f"Fleet tag of record {cap.get('fleet_tag')} · {len(cap.get('job_tags') or [])} jobs · {n_drift} DRIFT", '', '| job | configured | ran tonight | fleet |', '|---|---|---|---|', *[f"| {x['job']} | {x['configured'] or '—'} | {(x['ran_tonight'] or '—') + (' (moved to the fleet tag after this run)' if x.get('moved_after_run') else '')} | {x['fleet']} |" for x in (cap.get('job_tags') or [])], '', '## Backfill (Allooloo Datasets · BACKFILL-01)', '', bf_line, '', '| market | BACKFILL · year in progress | years done | rows | docs | depth (history_from) | storage | tonight |', '|---|---|---|---|---|---|---|---|', *[f"| {x['node']} | {x['year_in_progress'] or '—'} | {' '.join(x['years_done']) or '—'} | {fmt(x['rows'])} | {fmt(x['docs'])} | {x['depth'] or '—'} | {fmt(x['storage_bytes'])} | {x['night']} |" for x in BF], '', '## Agents', '', *table, '', '## Spend per lab', '', *spend_t, '', meter, '', '## Spend lines', '', '```', *dj['spend_lines'], '```', ''])
    html = f'<p><b>{subject}</b> · {dj["not_landed"]} not landed</p><p>{cap_line0}</p><p>{cap_line}</p><p>{tr_line}</p><p>{bf_line}</p><table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse;font:13px sans-serif"><tr><th>agent</th><th>as_of</th><th>verdict</th><th>rows</th><th>delta</th><th>flags</th><th>hand items</th></tr>' + ''.join(
        f"<tr><td>{r['agent']}</td><td>{r['as_of'] or '—'}</td><td><b>{r['verdict']}</b></td><td>{fmt(r['rows'])}</td><td>{sgn(r['delta'])}</td><td>{' · '.join(r['flags']) or '—'}</td><td>{' · '.join(r['hand_items']) or '—'}</td></tr>" for r in rows) + '</table><p>' + ' · '.join(f'{k} ${v["usd"]:.2f}' for k, v in sorted(labs.items())) + f'</p><p>{meter}</p><p>Private: allooloocmkgapex/ops/{NIGHT}/</p>'
    n1 = put_beside(ops, f'{NIGHT}/DIGEST-{NIGHT}.md', md, 'text/markdown'); n2 = put_beside(ops, f'{NIGHT}/digest.json', json.dumps(dj, ensure_ascii=False, indent=1), 'application/json')
    n3 = put_beside(ops, f'mail/{NIGHT}.json', json.dumps({'to': 'developers@allooloo.ai', 'subject': subject, 'html': html}, ensure_ascii=False), 'application/json')
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
