"""AMF BDIF (Base des décisions et informations financières) — the regulated-information trail per French issuer through the public API behind
bdif.amf-france.org: GET /back/api/v1/informations?Jetons=<AMF filer token>&DateDebut=<since>&DateFin=<today>&From=&Size= (the token comes from
Width 0, name-exact against the filers named in the last 10,000 BDIF items). Every item carries its publication date, information types (FT financial
information, DD document filings, OPA offers, VISA prospectus visas, SPDE …), document types, title and the BDIF page. Read-by: 'AMF BDIF regulatory-
information database (per filer token)'. Register rows are the issuer's own record: exempt from the name rule."""
from common import *
API = 'https://bdif.amf-france.org/back/api/v1/informations'
TYPE = {'FT': 'results', 'DD': 'regulatory_filing', 'OPA': 'takeover', 'VISA': 'prospectus', 'SPDE': 'regulatory_filing', 'DP': 'prospectus', 'RA': 'results', 'RF': 'results', 'AG': 'agm_egm', 'DEC': 'regulatory_filing', 'FRANC': 'major_holder', 'DIR': 'directors_dealings'}
DOC = {'DocumentReferenceEnregistrement': 'results', 'RapportFinancierAnnuel': 'results', 'RapportFinancierSemestriel': 'results', 'InformationTrimestrielle': 'results', 'DeclarationFranchissementSeuil': 'major_holder', 'DeclarationDirigeant': 'directors_dealings', 'DeclarationDirigeants': 'directors_dealings', 'DeclarationFranchissementSeuils': 'major_holder', 'ObligationDepotOP': 'takeover', 'NoteOperation': 'prospectus', 'Prospectus': 'prospectus', 'AvisConvocationAG': 'agm_egm', 'DescriptifProgrammeRachat': 'corporate_news', 'InformationReglementee': 'regulatory_filing'}
def fetch(r):
    tok = (r.get('amf_token') or '').strip()
    if not tok: return {'gap': 'no AMF filer token in Width 0 (not among the filers of the last 10,000 BDIF items)', 'events': []}
    evs = []; seen = set(); From = 0; total = None
    while From < 2000:
        x = get(API, params={'Jetons': tok, 'DateDebut': SINCE.isoformat(), 'DateFin': TODAY.isoformat(), 'From': From, 'Size': 100}, headers={'Accept': 'application/json'}, timeout=60)
        if x is None or x.status_code != 200: break
        j = x.json(); res = j.get('result') or []; total = j.get('total')
        for it in res:
            num = it.get('numero') or it.get('numeroConcatene') or ''
            if not num or num in seen: continue
            seen.add(num); dt = to_iso((it.get('datePublication') or it.get('dateMiseEnLigne') or '')[:10])
            if not in_window(dt): continue
            ti = it.get('typesInformation') or []; td = it.get('typesDocument') or []
            et = next((DOC[d] for d in td if d in DOC), None) or next((TYPE[t] for t in ti if t in TYPE), 'regulatory_filing')
            title = (it.get('titre') or '') or (', '.join(td) or ', '.join(ti) or 'BDIF item')
            names = [s.get('raisonSociale') for s in (it.get('societes') or []) if s.get('jeton') == tok]
            docs = it.get('documents') or []
            evs.append(event(r, et, dt, f"{title} [{', '.join(ti)}]"[:300], 'AMF BDIF regulatory information', f'https://bdif.amf-france.org/#/information/{num}', 'AMF BDIF regulatory-information database (per filer token)', wire='AMF BDIF', detail=f"types {', '.join(td)}; documents {len(docs)}; filer {names[0] if names else tok}", category=', '.join(ti), reference=num, language=(it.get('langue') or '').lower()))
        if len(res) < 100: break
        From += 100
    return {'events': evs, 'n': len(evs), 'total_items': total}
issuers = load_issuers()
if __name__ == '__main__':
    run_workers('bdif_events', fetch, issuers, threads=4)
