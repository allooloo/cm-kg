"""Pass 2.2 — Claude adjudicates the Width 0 pockets from cited evidence, or leaves the field blank with a one-line reason. Label 'adjudicated by Claude'.
  (a) LEI conflicts: the GLEIF mapping file mapped the ISIN to an LEI whose legal name is another entity. Evidence: that LEI's record, GLEIF candidates for the
      issuer's own name, the register row. Ruling: the LEI that IS the issuer, or blank.
  (b) SIREN gaps: issuers without an SIREN (no LEI registeredAs at RCS, no name-exact register row). Evidence: RCS / RNE register (State company search) candidates whose name shares the issuer's key
      tokens (public companies), the GLEIF record, the exchange short name. Ruling: the SIREN that IS the issuer (same legal entity), or blank (overseas, trust, name differs).
  (c) Nothing for auditors at Width 0 (the annual report is a source link only); the ChatGPT read fills auditor in pass 2.3."""
import re
from fc_common import *
from collections import Counter
issuers = load_issuers(); byk = {key(r): r for r in issuers}
rows = {r['_tab'] + '|' + r['ISIN']: r for r in all_rows()}
lei_rec = {d['key']: d for d in pond.read_jsonl_all(NODE, 'width0', 'lei_records.jsonl', key='key')}
lei_match = {d['name']: d for d in pond.read_jsonl_all(NODE, 'width0', 'lei_match.jsonl', key='name')}
isin_lei = pond.read_json_latest(NODE, 'width0', 'isin_lei_hits.json') or {}
RCS = {d['key']: d for d in pond.read_jsonl_all(NODE, 'width0', 'lei_records.jsonl', key='key')}
SYS = ("You are the reader of record for a capital-markets identity registry. You answer only from the evidence given. You never guess. "
       "A subsidiary, trustee, responsible entity, registry or adviser is NOT the issuer. If the evidence does not settle the question, say so. Reply with strict JSON only.")
def gleif_lookup(lei):
    r = get(f'https://api.gleif.org/api/v1/lei-records/{lei}', headers={'Accept': 'application/vnd.api+json'}, tries=2)
    if r is None or r.status_code != 200: return {}
    a = r.json()['data']['attributes']; e = a['entity']
    return {'lei': lei, 'name': e['legalName']['name'], 'jurisdiction': e.get('jurisdiction'), 'registeredAs': e.get('registeredAs'), 'registeredAt': (e.get('registeredAt') or {}).get('id'), 'legal_address': e['legalAddress'], 'status': e.get('status')}
def rule_lei(r):
    k = key(r); mapped = isin_lei.get(r['isin'], '').split('|')[0]
    ev = [f"Issuer on the exchange list: {r['name']} ({r['exchange']}: {r['ticker']}), ISIN {r['isin']}, SIREN {r.get('acn') or 'none'}.",
          f"GLEIF mapping file says ISIN {r['isin']} -> LEI {mapped}; that LEI's record: {json.dumps(lei_rec.get(mapped) or gleif_lookup(mapped))[:900]}"]
    m = lei_match.get(r['name']) or {}; cands = [c for c in (m.get('cands') or []) if c[1]][:8]
    if not cands:
        x = get('https://api.gleif.org/api/v1/fuzzycompletions', params={'field': 'entity.legalName', 'q': r['name'][:100]}, headers={'Accept': 'application/vnd.api+json'}, tries=2)
        if x is not None and x.status_code == 200: cands = [(c['attributes']['value'], (c.get('relationships') or {}).get('lei-records', {}).get('data', {}).get('id')) for c in x.json().get('data', [])][:8]
    for v, l in cands[:5]:
        if l: ev.append(f"GLEIF candidate for the issuer name: {v} -> {l}: {json.dumps(gleif_lookup(l))[:500]}")
    a = RCS.get(r.get('reg_id') or '')
    if a: ev.append(f"RCS / RNE register (State company search): SIREN {a['reg_id']} {a['name']} type {a.get('entity_type')} / {a.get('company_type')} status {a.get('status')}")
    prompt = ("Question: which LEI identifies THIS issuer (the listed legal entity itself)? The mapping-file LEI belongs to an entity with a different legal name — decide whether that entity is the issuer under a former/current name, "
              "or a different entity (trustee, responsible entity, subsidiary, parent). Rule only if the evidence settles it.\n\nEVIDENCE:\n" + '\n'.join(ev)[:12000] +
              '\n\nReply JSON: {"lei": "<LEI or empty>", "mapped_lei_is": "issuer|other_entity|unclear", "confidence": "high|medium|low", "reason": "<one line>", "source": "<URL that settles it or empty>"}')
    res = claude(prompt, SYS); j = jparse(res.get('text', '')) or {}
    return {'field': 'LEI', 'ruling': j.get('lei', ''), 'mapped_lei': mapped, 'mapped_lei_is': j.get('mapped_lei_is', ''), 'confidence': j.get('confidence', ''), 'reason': j.get('reason', ''), 'source': j.get('source', ''), 'usage': res.get('usage'), 'error': res.get('error')}
def name_key(s):
    s = (s or '').upper().replace('&', ' AND ').replace('.', '').replace(',', '')
    s = re.sub(r'\bLIMITED\b', 'LTD', s); s = re.sub(r'\bPRIVATE\b', 'PTE', s)
    return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s).split())
toks_index = {}
def rule_acn(r):
    k = key(r); row = rows.get(k, {}); rec = lei_rec.get(row.get('LEI') or '', {})
    kt = [w for w in norm(r['name']).split() if w not in STOP and len(w) >= 4]
    cands = set()
    for t in kt[:2]: cands |= toks_index.get(t, set())
    cands = [RCS[c] for c in cands if all(t in norm(RCS[c]['name']) for t in kt[:2])][:8] if kt else []
    ev = [f"Issuer on the exchange list: {r['name']} ({r['exchange']}: {r['ticker']}), ISIN {r['isin']}; trading name {r.get('trading_name') or ''}; address on record: {row.get('Registered office') or ''}; GLEIF jurisdiction {rec.get('jur') or ''}, GLEIF registeredAs {rec.get('registeredAs') or ''} at {rec.get('registeredAt') or ''}.",
          "RCS candidates (public companies and foreign-company branches) sharing the issuer's name tokens: " + json.dumps([{'reg_id': c['reg_id'], 'name': c['name'], 'entity_type': c.get('entity_type'), 'company_type': c.get('company_type'), 'status': c.get('status'), 'incorporated': c.get('incorporated'), 'former': c.get('former_names', [])[:3]} for c in cands])[:3500]]
    prompt = ("Question: which SIREN is THIS listed issuer's own RCS registration? Accept only the same legal entity (its current or former name). A trustee, manager, "
              "subsidiary or a similarly named private company is NOT the issuer. Issuers incorporated outside France (Bermuda, Cayman, BVI, Hong Kong, China, Malaysia, Australia …) "
              "carry a SIREN only when registered as a foreign-company branch — say so and leave the SIREN empty when no branch row is the issuer.\n\nEVIDENCE:\n" + '\n'.join(ev)[:9000] +
              '\n\nReply JSON: {"uen": "<SIREN or empty>", "why_blank": "overseas|trust|name_differs|no_candidate|unclear|", "confidence": "high|medium|low", "reason": "<one line>"}')
    res = claude(prompt, SYS); j = jparse(res.get('text', '')) or {}
    acn = re.sub(r'[^A-Z0-9]', '', (j.get('reg_id', '') or j.get('acn', '') or '').upper())
    return {'field': 'SIREN', 'ruling': acn if acn in RCS else '', 'why_blank': j.get('why_blank', ''), 'confidence': j.get('confidence', ''), 'reason': j.get('reason', ''), 'source': RCS[acn]['src'] if acn in RCS else '', 'candidates': [c['reg_id'] for c in cands], 'usage': res.get('usage'), 'error': res.get('error')}
if __name__ == '__main__':
    lei_items = [byk[k] for k, row in rows.items() if k in byk and (row.get('LEI State') or '') == 'conflict']
    acn_items = []  # register-id gaps: no candidate index for this node (RCS / Handelsregister have no bulk file); the LEI record route stands
    print('LEI conflicts', len(lei_items), '| SIREN gaps', len(acn_items), flush=True)
    resume('claude_lei', rule_lei, lei_items, threads=3)
    resume('claude_acn', rule_acn, acn_items, threads=3)
