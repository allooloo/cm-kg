"""Step 3 (local) — LEI for every roster line from the GLEIF golden copy extract (POND\\estate\\gleif-golden\\<date>\\lei-JP.jsonl + lei-index-JP.json),
no API rate limit. Route a) registeredAs = the 12-digit company registration number inside the EDINET corporate number (法人番号 minus its leading
check digit, written XXXX-XX-XXXXXX) at RA000412 — exact, no name matching. Route b) for lines without a corporate number: the JPX / EDINET English
name equal (after normalisation) to a GLEIF legal or other name of a JP-jurisdiction record — 'GLEIF name-exact'. Looser matches stay in Gaps.
Writes raw/lei_match.jsonl (the same shape the API route writes) keyed by symbol; an earlier API-route file is kept beside it as lei_match_api.jsonl."""
import json, re, os, sys, shutil
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS'); import pond
from collections import Counter
rows = json.load(open('raw/roster.json', encoding='utf-8'))
gp = pond.latest('estate', 'gleif-golden', 'lei-JP.jsonl'); ip = pond.latest('estate', 'gleif-golden', 'lei-index-JP.json'); assert gp and ip, 'run gleif-golden/extract.py first'
recs = {}
for line in open(gp, encoding='utf-8'):
    d = json.loads(line); recs[d['lei']] = d
idx = json.load(open(ip, encoding='utf-8')); RA = idx['registeredAs']; NM = idx['name']; gmeta = json.load(open(pond.latest('estate', 'gleif-golden', 'golden.meta.json')))
def norm(s): return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', (s or '').upper().replace('&', ' AND ')).split())
def norm_loose(s): return ' '.join(w for w in norm(s).split() if w not in {'CO', 'LTD', 'INC', 'CORP', 'CORPORATION', 'COMPANY', 'LIMITED', 'KK', 'KABUSHIKI', 'KAISHA', 'HOLDINGS', 'HOLDING', 'GROUP', 'THE'})
NML = {}
for k, v in NM.items():
    kl = norm_loose(k)
    if kl: NML.setdefault(kl, []).extend(v)
def reg_key(cn):
    cn = re.sub(r'\D', '', cn or ''); return f'{cn[1:5]}-{cn[5:7]}-{cn[7:]}' if len(cn) == 13 else ''
def active(c): return c['status'] == 'ACTIVE' and c['reg_status'] in ('ISSUED', 'PENDING_TRANSFER', 'PENDING_ARCHIVAL')
def pub(c): return {'lei': c['lei'], 'name': c['name'], 'jur': c['jur'], 'status': c['status'], 'reg_status': c['reg_status'], 'registeredAs': c['registeredAs'], 'registeredAt': c['registeredAt']}
out = []; src_label = f"GLEIF golden copy {gmeta['publish_date'][:10]}"
for r in rows:
    key = r['exchange'] + '|' + r['symbol']; rk = reg_key(r.get('corporate_number')); d = None
    if rk:
        c = [recs[l] for l in RA.get(rk, []) if l in recs and (recs[l]['registeredAt'] == 'RA000412' or recs[l]['jur'].startswith('JP'))]
        if len(c) == 1: d = {'key': key, 'lei': c[0]['lei'], 'match': f'GLEIF registeredAs = EDINET corporate number (RA000412; {src_label})', 'route': 'registeredAs', 'registeredAs': rk, 'rec': pub(c[0])}
        elif len(c) > 1:
            a = [x for x in c if active(x)]
            d = {'key': key, 'lei': a[0]['lei'], 'match': f'GLEIF registeredAs = EDINET corporate number (one active record among duplicates; {src_label})', 'route': 'registeredAs', 'registeredAs': rk, 'rec': pub(a[0])} if len(a) == 1 else {'key': key, 'lei': '', 'gap': 'several GLEIF records carry this company registration number: ' + ', '.join(x['lei'] for x in c[:5]), 'route': 'registeredAs', 'registeredAs': rk}
        gap0 = f'no GLEIF record registered as {rk} (RA000412)'
    else: gap0 = 'foreign issuer: no Japanese corporate number' if r.get('foreign') else 'no corporate number on the roster line (no EDINET filer joined)'
    if d is None:
        names = [n for n in (r.get('name'), r.get('name_en_edinet')) if n]; c = []
        for n in names:
            for l in NM.get(norm(n), []):
                if l in recs and recs[l] not in c: c.append(recs[l])
        if not c:
            for n in names:
                for l in NML.get(norm_loose(n), []):
                    if l in recs and recs[l] not in c: c.append(recs[l])
        if not r.get('foreign'): c = [x for x in c if x['jur'].startswith('JP')]
        if len(c) > 1 and len([x for x in c if active(x)]) == 1: c = [x for x in c if active(x)]
        if len(c) == 1: d = {'key': key, 'lei': c[0]['lei'], 'match': f"GLEIF name-exact (English name against the legal or other names{'' if r.get('foreign') else ', jurisdiction JP'}; {src_label})", 'route': 'name', 'rec': pub(c[0])}
        elif len(c) > 1: d = {'key': key, 'lei': '', 'gap': 'several GLEIF records match the English name exactly: ' + ', '.join(x['lei'] for x in c[:5]), 'route': 'name'}
        else: d = {'key': key, 'lei': '', 'gap': gap0 + '; no GLEIF record with the exact English name', 'route': 'name'}
    out.append(d)
if os.path.exists('raw/lei_match.jsonl') and not os.path.exists('raw/lei_match_api.jsonl'): shutil.move('raw/lei_match.jsonl', 'raw/lei_match_api.jsonl')
with open('raw/lei_match.jsonl', 'w', encoding='utf-8') as f:
    for d in out: f.write(json.dumps(d, ensure_ascii=False) + '\n')
print('lei_match (local) matched', sum(1 for d in out if d.get('lei')), 'of', len(out), Counter(d.get('route') for d in out if d.get('lei')), '| gaps', Counter((d.get('gap') or '')[:40] for d in out if not d.get('lei')).most_common(4))
