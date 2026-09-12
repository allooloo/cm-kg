"""Swiss commercial-register events from the SHAB / FOSC (Swiss Official Gazette of Commerce) public publications API: GET https://www.shab.ch/api/v1/publications
with rubric HR (commercial register), a keyword and a date window, per issuer that carries a Zefix UID. A publication is taken only when its title or text
names the issuer's UID (CHE-…) or its registered name; sub-rubric HR01 = new registration, HR02 = mutation (capital, board, purpose, name, seat …),
HR03 = deletion. URL = the publication's own page https://www.shab.ch/#!/search/publications/detail/<id>; the XML export is the machine record.
Read-by: 'SHAB publications API (Swiss Official Gazette of Commerce, commercial-register rubric)'. Registry rows are the issuer's own record: exempt from the name rule."""
import re
from common import *
API = 'https://www.shab.ch/api/v1/publications'
SUB = {'HR01': 'register_new_registration', 'HR02': 'register_mutation', 'HR03': 'register_deletion'}
def fetch(r):
    uid = (r.get('reg_id') or '').strip()
    if not uid: return {'gap': 'no Zefix UID in Width 0', 'events': []}
    uid_key = re.sub(r'[^A-Z0-9]', '', uid.upper()); evs = []; seen = set(); n_seen = 0
    for kw in [uid, r.get('full_name') or r['name']]:
        for page in range(0, 4):
            x = get(API, params={'publicationStates': 'PUBLISHED', 'rubrics': 'HR', 'keyword': kw, 'publicationDate.start': SINCE.isoformat(), 'publicationDate.end': TODAY.isoformat(), 'pageRequest.size': 50, 'pageRequest.page': page}, headers={'Accept': 'application/json'}, timeout=60)
            if x is None or x.status_code != 200: break
            j = x.json(); items = j.get('content') or []
            for it in items:
                m = it.get('meta') or {}; pid = m.get('id'); n_seen += 1
                if not pid or pid in seen: continue
                title = m.get('title', {}).get('en') or m.get('title', {}).get('de') or m.get('title', {}).get('fr') or ''
                blob = json.dumps(it, ensure_ascii=False)
                if uid_key not in re.sub(r'[^A-Z0-9]', '', blob.upper()) and not name_in(title, r['name'], (r.get('full_name'),)): continue
                seen.add(pid); dt = to_iso((m.get('publicationDate') or '')[:10]); sub = m.get('subRubric') or ''
                if not in_window(dt): continue
                evs.append(event(r, SUB.get(sub, 'register_mutation'), dt, f"{sub} {title}".strip() or f'SHAB {sub}', 'SHAB / FOSC commercial register publication', f'https://www.shab.ch/#!/search/publications/detail/{pid}', 'SHAB publications API (Swiss Official Gazette of Commerce, commercial-register rubric)', detail=f"publication {m.get('publicationNumber', '')}; office {((m.get('registrationOffice') or {}).get('displayName') or '')[:80]}", category=sub, reference=m.get('publicationNumber', ''), language=m.get('language', '')))
            if len(items) < 50: break
    return {'events': evs, 'n': len(evs), 'publications_seen': n_seen}
issuers = load_issuers()
if __name__ == '__main__':
    run_workers('shab_events', fetch, issuers, threads=4)
