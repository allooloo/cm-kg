r"""eco_history.py — BACKFILL-01 B-1 (DAY ORDER 7, 2026-10-25): the ECO register's dated history, and rule_in_force(cc, date) over it.
The register of record is each market's signed Electronic Compliance Object (https://<cc>-eco.ai/eco.json: build, sha256, signature kid). A version of the
rule enters the history only with a sourced in-force date:
  · the record itself, in force from the day it was hunted (record.hunted) — what the register has read;
  · an earlier in-force date only where the record's own sources state one (IN_FORCE below, each with the page it is read on and the words).
rule_in_force(cc, d) = the latest entry in force on d. A date before every entry gets None and the gap, so a 2021 row never carries a 2026 rule.
Writes eco_history.json beside. Usage: python -X utf8 -I eco_history.py"""
import os, sys, json, urllib.request, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import roster
H = os.path.join(HERE, 'eco_history.json')
# sourced in-force dates, read from the ECO record's own pages (policy keyed by market; a market with none has its hunt date only)
IN_FORCE = {
 'ca': [{'rule': 'NI 51-102 Continuous Disclosure Obligations, as consolidated June 9, 2023 (deadlines: annual 90/120 days, interim 45/60 days)', 'in_force_from': '2023-06-09',
         'source': 'https://www.bcsc.bc.ca/-/media/PWS/New-Resources/Securities-Law/Instruments-and-Policies/Policy-5/51102-NI-July-25-2023.pdf',
         'words': 'ca-eco.ai record notes: "Deadlines are for NI 51-102 as consolidated June 9, 2023 on the BCSC site"'}],
}
UA = {'User-Agent': 'Allooloo backfill (BACKFILL-01 eco_history)', 'accept': 'application/json'}
def build():
    out = {'built': datetime.date.today().isoformat(), 'register': 'https://<cc>-eco.ai/eco.json', 'markets': {}}
    for n in roster.load():
        cc = roster.cc_of(n)
        try: e = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://{cc}-eco.ai/eco.json', headers=UA), timeout=30).read())
        except Exception as x: out['markets'][cc] = {'entries': [], 'gap': f'ECO record not read ({x!r:.80})'}; continue
        rec = e.get('record') or {}; sig = e.get('signature') or {}
        ver = {'eco': f'{cc}-eco.ai', 'eco_build': e.get('build') if isinstance(e.get('build'), str) else (e.get('build') or {}).get('file') or (e.get('build') or {}).get('id'), 'eco_sha256': e.get('sha256'), 'eco_kid': sig.get('kid') if isinstance(sig, dict) else None}
        ents = [{**ver, **x} for x in IN_FORCE.get(cc, [])]
        ents.append({**ver, 'rule': f'{rec.get("country") or cc} disclosure regime as read by the ECO record (regulator, periodic and ad hoc regime)', 'in_force_from': rec.get('hunted'), 'source': f'https://{cc}-eco.ai/eco.json', 'words': 'the record\'s hunt date: the register holds no earlier dated version'})
        out['markets'][cc] = {'entries': sorted([x for x in ents if x.get('in_force_from')], key=lambda x: x['in_force_from'])}
    json.dump(out, open(H, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); return out
_H = None
def rule_in_force(cc, d):
    global _H
    if _H is None: _H = json.load(open(H, encoding='utf-8'))
    ents = [x for x in (_H['markets'].get(cc) or {}).get('entries', []) if x['in_force_from'] <= d]
    if not ents:
        first = ((_H['markets'].get(cc) or {}).get('entries') or [{}])[0].get('in_force_from')
        return None, f'the ECO register holds no version of the {cc} rule in force on {d} (its dated history begins {first or "nowhere"}); blank, never a later rule'
    x = ents[-1]; return {k: x.get(k) for k in ('eco', 'eco_build', 'eco_sha256', 'eco_kid', 'rule', 'in_force_from', 'source')}, None
if __name__ == '__main__':
    o = build(); print('eco history:', len(o['markets']), 'markets ·', sum(len(v.get('entries', [])) for v in o['markets'].values()), 'dated entries ->', H)
    print('ca 2025-03-01 ->', rule_in_force('ca', '2025-03-01')[0]['rule'][:60], '· ca 2022-01-01 ->', rule_in_force('ca', '2022-01-01')[1][:90])
