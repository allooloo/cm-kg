"""Step 3 (local) — LEI for every roster line from the GLEIF golden copy extract (POND\\estate\\gleif-golden\\<date>\\lei-KR.jsonl + lei-index-KR.json),
no API rate limit. Route a) registeredAs = the DART business registration number (bizr_no, 10 digits, written XXX-XX-XXXXX) — GLEIF registers Korean
companies at RA000657 with that number — exact, no name matching; route a2) the corporate registration number (jurir_no, 13 digits, written
XXXXXX-XXXXXXX) for records registered with it. Route b) the DART English name or the KIND Korean name equal (after normalisation) to a GLEIF
legal or other name of a KR-jurisdiction record — 'GLEIF name-exact'. Looser matches stay in Gaps. Writes raw/lei_match.jsonl keyed by symbol."""
import json, re, os, sys
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS'); import pond
from collections import Counter
rows = json.load(open('raw/roster.json', encoding='utf-8'))
gp = pond.latest('estate', 'gleif-golden', 'lei-KR.jsonl'); ip = pond.latest('estate', 'gleif-golden', 'lei-index-KR.json'); assert gp and ip, 'run gleif-golden/extract.py first'
recs = {}
for line in open(gp, encoding='utf-8'):
    d = json.loads(line); recs[d['lei']] = d
idx = json.load(open(ip, encoding='utf-8')); RA = idx['registeredAs']; NM = idx['name']; gmeta = json.load(open(pond.latest('estate', 'gleif-golden', 'golden.meta.json')))
RA_DIGITS = {}
for k, v in RA.items(): RA_DIGITS.setdefault(re.sub(r'\D', '', k), []).extend(v)
def norm(s): return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', (s or '').upper().replace('&', ' AND ')).split())
def norm_ko(s): return re.sub(r'[\s\(\)（）,.\-·]', '', (s or '')).replace('주식회사', '').replace('(주)', '')
NMK = {}
for k, v in NM.items():
    kk = norm_ko(k)
    if kk: NMK.setdefault(kk, []).extend(v)
def active(c): return c['status'] == 'ACTIVE' and c['reg_status'] in ('ISSUED', 'PENDING_TRANSFER', 'PENDING_ARCHIVAL')
def pub(c): return {'lei': c['lei'], 'name': c['name'], 'jur': c['jur'], 'status': c['status'], 'reg_status': c['reg_status'], 'registeredAs': c['registeredAs'], 'registeredAt': c['registeredAt']}
def pick(c, key, label, route, extra=None):
    if len(c) > 1 and len([x for x in c if active(x)]) == 1: c = [x for x in c if active(x)]; label += ' (one active record among duplicates)'
    if len(c) == 1: return {'key': key, 'lei': c[0]['lei'], 'match': label, 'route': route, 'rec': pub(c[0]), **(extra or {})}
    if len(c) > 1: return {'key': key, 'lei': '', 'gap': f'several GLEIF records match ({route}): ' + ', '.join(x['lei'] for x in c[:5]), 'route': route, **(extra or {})}
    return None
out = []; src_label = f"GLEIF golden copy {gmeta['publish_date'][:10]}"
for r in rows:
    key = r['exchange'] + '|' + r['symbol']; d = None; gap0 = []
    b = re.sub(r'\D', '', r.get('bizr_no') or '')
    if len(b) == 10:
        c = [recs[l] for l in RA_DIGITS.get(b, []) if l in recs and recs[l]['jur'].startswith('KR')]
        d = pick(c, key, f'GLEIF registeredAs = DART business registration number (RA000657; {src_label})', 'registeredAs', {'registeredAs': f'{b[:3]}-{b[3:5]}-{b[5:]}'})
        if d is None: gap0.append(f'no GLEIF record registered as {b[:3]}-{b[3:5]}-{b[5:]}')
    j = re.sub(r'\D', '', r.get('jurir_no') or '')
    if d is None and len(j) == 13:
        c = [recs[l] for l in RA_DIGITS.get(j, []) if l in recs and recs[l]['jur'].startswith('KR')]
        d = pick(c, key, f'GLEIF registeredAs = DART corporate registration number ({src_label})', 'registeredAs-jurir', {'registeredAs': f'{j[:6]}-{j[6:]}'})
        if d is None: gap0.append(f'no GLEIF record registered as {j[:6]}-{j[6:]}')
    if d is None:
        c = []
        for n in [r.get('name_en')]:
            for l in NM.get(norm(n), []) if n else []:
                if l in recs and recs[l] not in c: c.append(recs[l])
        for n in [r.get('name_ko')]:
            for l in NMK.get(norm_ko(n), []) if n else []:
                if l in recs and recs[l] not in c: c.append(recs[l])
        c = [x for x in c if x['jur'].startswith('KR')]
        d = pick(c, key, f'GLEIF name-exact (DART English name or KIND Korean name against the legal or other names, jurisdiction KR; {src_label})', 'name')
        if d is None: d = {'key': key, 'lei': '', 'gap': '; '.join(gap0 + ['no GLEIF record with the exact English or Korean name']), 'route': 'name'}
    out.append(d)
with open('raw/lei_match.jsonl', 'w', encoding='utf-8') as f:
    for d in out: f.write(json.dumps(d, ensure_ascii=False) + '\n')
print('lei_match (local) matched', sum(1 for d in out if d.get('lei')), 'of', len(out), Counter(d.get('route') for d in out if d.get('lei')), '| gaps', Counter((d.get('gap') or '')[:40] for d in out if not d.get('lei')).most_common(4))
