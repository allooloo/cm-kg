r"""build_halts.py — ENUM-01 (DAY ORDER 6, 2026-10-25): the halt-source policy of the acm-signals Worker (worker\halts.js, halts.json), generated for every
live node on the roster of record (list_nodes) from that market's own Electronic Compliance Object (https://<cc>-eco.ai/eco.json, field trading_halts_page).
Sourced or blank: a market whose ECO record says "not found" carries halts: null and the pages it checked. A roster node with no ECO record stops the build.
Replaces the twelve-market table written by patch_halt01.py (kept beside as .pre-enum01-20261025). Usage: python -X utf8 -I build_halts.py"""
import os, sys, json, shutil, urllib.request, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'RAILS', 'job')); import roster
UA = {'User-Agent': 'Allooloo digest (ENUM-01 build_halts)', 'accept': 'application/json'}
out, gaps = {}, []
for n in roster.load():
    cc = roster.cc_of(n)
    try: rec = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://{cc}-eco.ai/eco.json', headers=UA), timeout=30).read())
    except Exception as e: gaps.append(f'{cc}: no ECO record ({e!r:.60})'); continue
    f = ((rec.get('record') or {}).get('fields') or {}).get('trading_halts_page') or {}
    out[cc] = {'country': n['country'], 'halts': (f.get('url') or f.get('source')) if f.get('state') in ('sourced', 'confirmed', 'filled') else None, 'halts_checked': f.get('checked') or [], 'halts_note': f.get('value'), 'eco': f'https://{cc}-eco.ai/'}
if gaps: raise SystemExit('ROSTER POLICY GAP · halt source (ECO record) · ' + '; '.join(gaps) + ' — build refused')
day = datetime.date.today().strftime('%Y%m%d')
for name in ('worker/halts.js', 'halts.json'):
    p = os.path.join(HERE, name)
    if os.path.exists(p) and not os.path.exists(p + '.pre-enum01-' + day): shutil.copy2(p, p + '.pre-enum01-' + day)
head = f'// the halts page of each live market on the roster of record (list_nodes), read from its Electronic Compliance Object (<cc>-eco.ai/eco.json) by build_halts.py, {datetime.date.today().isoformat()} (ENUM-01)\n'
open(os.path.join(HERE, 'worker', 'halts.js'), 'w', encoding='utf-8', newline='\n').write(head + 'export const HALTS = ' + json.dumps(out, ensure_ascii=False) + ';\n')
json.dump(out, open(os.path.join(HERE, 'halts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('halts policy:', len(out), 'markets ·', sum(1 for v in out.values() if v['halts']), 'with a sourced halts page ·', sum(1 for v in out.values() if not v['halts']), 'blank (not found on the record)')
