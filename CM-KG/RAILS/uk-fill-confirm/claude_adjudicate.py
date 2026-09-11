"""Pass 2.2 — Claude adjudicates the Width 0 pockets from the cited evidence, or leaves the field blank with a one-line reason. Label 'adjudicated by Claude'.
  (a) LEI conflicts: the GLEIF mapping file mapped the issuer's ISIN to an LEI whose legal name is another entity (87 rows). Evidence: the GLEIF record of that
      LEI, GLEIF fuzzy candidates for the issuer's own name, the Companies House profile. Ruling: the LEI that IS the issuer, or blank.
  (b) Unmatched Companies House rows (393): the Companies House API name search (top 10), the Width 0 profile address/country, GLEIF record. Ruling: the number
      that IS the issuer (exact legal entity, not a subsidiary), or blank with reason (overseas incorporation, fund, name differs).
  (c) Auditor strings read by regex that canonicalised to no recognised firm, or tied (Width 0 Gaps). Ruling from the cited page."""
import re
from fc_common import *
from collections import Counter
issuers = load_issuers(); byk = {key(r): r for r in issuers}
rows = {r['_tab'] + '|' + r['Ticker (TIDM)']: r for r in all_rows()}
lei_rec = {d['key']: d for d in jload(W0 + r'\lei_records.jsonl')}
lei_match = {d['name']: d for d in jload(W0 + r'\lei_match.jsonl')}
isin_lei = json.load(open(W0 + r'\isin_lei_hits.json'))
chapi = {d['key']: d for d in jload(W0 + r'\ch_api.jsonl')}
reg0 = {d['key']: d for d in jload(W0 + r'\enr_reg.jsonl')}
_src = open(r'C:\ALLOOLOO\CM-KG\RAILS\uk-width0\assemble.py', encoding='utf-8').read()
KNOWN_AUD = eval(re.search(r'^KNOWN_AUD = (\[.*?\])\s*$', _src, re.M | re.S).group(1))
KNOWN_SET = set(c for c, _ in KNOWN_AUD)
def canon_aud(name):
    for canon, pat in KNOWN_AUD:
        if re.search(pat, name): return canon
    return name
SYS = ("You are the reader of record for a capital-markets identity registry. You answer only from the evidence given. You never guess. "
       "A subsidiary, parent, registrar or adviser is NOT the issuer. If the evidence does not settle the question, say so. Reply with strict JSON only.")
def gleif_lookup(lei):
    r = get(f'https://api.gleif.org/api/v1/lei-records/{lei}', headers={'Accept': 'application/vnd.api+json'}, tries=2)
    if r is None or r.status_code != 200: return {}
    a = r.json()['data']['attributes']; e = a['entity']
    return {'lei': lei, 'name': e['legalName']['name'], 'jurisdiction': e.get('jurisdiction'), 'registeredAs': e.get('registeredAs'), 'legal_address': e['legalAddress'], 'status': e.get('status'), 'reg_status': a['registration'].get('status')}
def rule_lei(r):
    k = key(r); row = rows.get(k, {}); mapped = isin_lei.get(r['isin'], '').split('|')[0]
    ev = [f"Issuer on the exchange list: {r['name']} ({r['exchange']}: {r['ticker']}), ISIN {r['isin']}.",
          f"GLEIF mapping file says ISIN {r['isin']} -> LEI {mapped}; that LEI's record: {json.dumps(lei_rec.get(mapped) or gleif_lookup(mapped))[:900]}"]
    m = lei_match.get(r['name']) or {}
    cands = [c for c in (m.get('cands') or []) if c[1]][:8]
    if not cands:
        x = get('https://api.gleif.org/api/v1/fuzzycompletions', params={'field': 'entity.legalName', 'q': r['name'][:100]}, headers={'Accept': 'application/vnd.api+json'}, tries=2)
        if x is not None and x.status_code == 200:
            cands = [(c['attributes']['value'], (c.get('relationships') or {}).get('lei-records', {}).get('data', {}).get('id')) for c in x.json().get('data', [])][:8]
    for v, l in cands[:5]:
        if l: ev.append(f"GLEIF candidate for the issuer name: {v} -> {l}: {json.dumps(gleif_lookup(l))[:500]}")
    a = chapi.get(k, {})
    if a.get('number'): ev.append(f"Companies House: number {a['number']}, profile {json.dumps(a.get('profile') or {})[:500]}")
    prompt = ("Question: which LEI identifies THIS issuer (the listed legal entity itself)? The mapping-file LEI belongs to an entity with a different legal name — "
              "decide whether that entity is the issuer under a former/current name, or a different entity (registrar, subsidiary, parent). Rule only if the evidence settles it.\n\nEVIDENCE:\n" + '\n'.join(ev)[:12000] +
              '\n\nReply JSON: {"lei": "<LEI or empty>", "mapped_lei_is": "issuer|other_entity|unclear", "confidence": "high|medium|low", "reason": "<one line>", "source": "<URL that settles it or empty>"}')
    res = claude(prompt, SYS); j = jparse(res.get('text', '')) or {}
    return {'field': 'LEI', 'ruling': j.get('lei', ''), 'mapped_lei': mapped, 'mapped_lei_is': j.get('mapped_lei_is', ''), 'confidence': j.get('confidence', ''), 'reason': j.get('reason', ''), 'source': j.get('source', ''), 'usage': res.get('usage'), 'error': res.get('error')}
def rule_ch(r):
    k = key(r); row = rows.get(k, {})
    s = ch_api('/search/companies', q=r['name'], items_per_page=10) or {}
    items = [{'number': it.get('company_number'), 'title': it.get('title'), 'type': it.get('company_type'), 'status': it.get('company_status'), 'address': (it.get('address') or {}).get('locality'), 'incorporated': it.get('date_of_creation')} for it in s.get('items', [])]
    rec = lei_rec.get(row.get('LEI') or '', {})
    ev = [f"Issuer on the exchange list: {r['name']} ({r['exchange']}: {r['ticker']}), ISIN {r['isin']}, exchange profile address: {row.get('Registered office') or ''}; country of incorporation on the exchange profile / GLEIF jurisdiction: {row.get('Incorporation jurisdiction') or ''}.",
          f"GLEIF record for the issuer's LEI: {json.dumps({kk: rec.get(kk) for kk in ('name', 'jur', 'legal_city', 'legal_country', 'registeredAs', 'registeredAt')})}",
          f"Companies House API name search results: {json.dumps(items)[:3000]}"]
    prompt = ("Question: which Companies House company number is THIS listed issuer's own registration? Accept only the same legal entity (a PLC or company whose name is the "
              "issuer's current or former name at the issuer's address). A UK subsidiary or holding company with a similar name is NOT the issuer. Issuers incorporated outside the UK "
              "(Jersey, Guernsey, Isle of Man, Ireland, Bermuda, BVI, Cayman, ...) have no Companies House registration unless registered as an overseas company (FC prefix) — then say so.\n\nEVIDENCE:\n" + '\n'.join(ev)[:9000] +
              '\n\nReply JSON: {"number": "<company number or empty>", "why_blank": "overseas|fund|name_differs|no_candidate|unclear|", "confidence": "high|medium|low", "reason": "<one line>"}')
    res = claude(prompt, SYS); j = jparse(res.get('text', '')) or {}
    return {'field': 'Companies House number', 'ruling': j.get('number', ''), 'why_blank': j.get('why_blank', ''), 'confidence': j.get('confidence', ''), 'reason': j.get('reason', ''), 'source': 'https://api.company-information.service.gov.uk/search/companies?q=' + requests.utils.quote(r['name']), 'candidates': items, 'usage': res.get('usage'), 'error': res.get('error')}
def rule_auditor(r):
    c = reg0.get(key(r), {}); cands = c.get('aud_cands') or {}
    ev = f"Evidence snippet from {c.get('aud_src')}: {c.get('aud_ev')}\n"
    if c.get('aud_src'):
        t, st = page_text(c['aud_src'])
        if t:
            i = t.lower().find('auditor'); ev += '\nPage excerpt:\n' + (t[max(0, i - 700):i + 900] if i >= 0 else t[:1500])
    prompt = (f"Issuer: {r['name']} ({r['exchange']}: {r['ticker']}). Strings read as a possible auditor: {list(cands)}.\n"
              "Question: which audit firm is named as THIS issuer's statutory auditor in the evidence? Give the firm's proper name (e.g. 'BDO LLP', 'PKF Littlejohn LLP', 'Crowe U.K. LLP'). "
              "If the evidence names no audit firm for this issuer, leave it empty.\n\nEVIDENCE:\n" + ev[:9000] + '\n\nReply JSON: {"auditor": "<firm or empty>", "confidence": "high|medium|low", "reason": "<one line>"}')
    res = claude(prompt, SYS); j = jparse(res.get('text', '')) or {}
    return {'field': 'Auditor', 'ruling': j.get('auditor', ''), 'confidence': j.get('confidence', ''), 'reason': j.get('reason', ''), 'source': c.get('aud_src', ''), 'usage': res.get('usage'), 'cands': cands, 'error': res.get('error')}
if __name__ == '__main__':
    lei_items = [byk[k] for k, row in rows.items() if k in byk and (row.get('LEI State') or '') == 'conflict']
    ch_items = [byk[k] for k, row in rows.items() if k in byk and not row.get('Companies House number')]
    aud_items = []
    for k, c in reg0.items():
        if k not in byk or (rows.get(k, {}).get('Auditor') or ''): continue
        cands = c.get('aud_cands') or {}
        if cands and not any(canon_aud(x) in KNOWN_SET for x in cands): aud_items.append(byk[k])
        elif 'conflict' in (c.get('aud_gap') or ''): aud_items.append(byk[k])
    print('LEI conflicts', len(lei_items), '| unmatched Companies House', len(ch_items), '| auditor unrecognised/conflict', len(aud_items), flush=True)
    resume('claude_lei', rule_lei, lei_items, threads=3)
    resume('claude_ch', rule_ch, ch_items, threads=3)
    resume('claude_auditor', rule_auditor, aud_items, threads=3)
