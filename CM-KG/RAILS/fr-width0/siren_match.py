"""Step 3 — the French company register through the State's public company search (recherche-entreprises.api.gouv.fr, no key; the register of record is
INPI / RNE, per-company Infogreffe pages sit behind a search UI — HITL note). Route 1: the GLEIF LEI record's registeredAs (SIREN at RA000189 / RA000190 =
INSEE / RCS) looked up by SIREN — exact by the registry. Route 2: name search, accepted only when the legal name equals the roster name after
normalisation (SA / SE / SCA / SAS spelling and punctuation). Kept: SIREN, legal name, legal form (nature juridique), NAF code, registered office
(siège), date of creation, administrative status, company category. Writes raw/siren.jsonl."""
import requests, json, re, os, time, threading
from concurrent.futures import ThreadPoolExecutor
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json'}
API = 'https://recherche-entreprises.api.gouv.fr/search'
rows = json.load(open('raw/roster.json', encoding='utf-8'))
LEIREC = {}
if os.path.exists('raw/lei_records.jsonl'):
    for line in open('raw/lei_records.jsonl', encoding='utf-8'):
        try: d = json.loads(line); LEIREC[d['key']] = d
        except Exception: pass
def name_key(s):
    s = (s or '').upper().replace('&', ' AND ').replace('.', '').replace(',', '').replace('-', ' ').replace("'", ' ')
    s = re.sub(r'\b(SA|SE|SCA|SAS|SARL|SOCIETE ANONYME|SOCIETE EUROPEENNE|GROUP|GROUPE|HOLDING|HOLDINGS|CIE|COMPAGNIE|ETS|ETABLISSEMENTS|LTD|PLC|NV|INC|CORP)\b', ' ', s)
    s = s.replace('É', 'E').replace('È', 'E').replace('Ê', 'E').replace('À', 'A').replace('Ç', 'C').replace('Ô', 'O').replace('Û', 'U').replace('Î', 'I')
    return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s).split())
def search(params):
    for i in range(4):
        try:
            r = requests.get(API, params=params, headers=UA, timeout=60)
            if r.status_code in (429, 502, 503): time.sleep(5 * (i + 1)); continue
            if r.status_code != 200: return None, r.status_code
            return r.json().get('results', []), 200
        except Exception: time.sleep(3 * (i + 1))
    return None, 'exhausted'
def pack(x, route):
    s = x.get('siege') or {}
    return {'siren': x.get('siren'), 'name': x.get('nom_raison_sociale') or x.get('nom_complet'), 'legal_form': x.get('nature_juridique'), 'naf': x.get('activite_principale'), 'created': x.get('date_creation'), 'status': x.get('etat_administratif'), 'category': x.get('categorie_entreprise'),
            'address': ', '.join(v for v in [s.get('adresse'), s.get('code_postal'), s.get('libelle_commune')] if v), 'city': s.get('libelle_commune'), 'department': s.get('departement'), 'region': s.get('region'), 'route': route, 'src': f"https://recherche-entreprises.api.gouv.fr/search?q={x.get('siren')}", 'annuaire': f"https://annuaire-entreprises.data.gouv.fr/entreprise/{x.get('siren')}"}
lock = threading.Lock()
def match(r):
    rec = LEIREC.get(r.get('lei') or '') or {}; ras = re.sub(r'\D', '', rec.get('registeredAs') or '')
    if len(ras) == 9:
        res, st = search({'q': ras, 'per_page': 3})
        hit = [x for x in (res or []) if x.get('siren') == ras]
        if hit: return {**pack(hit[0], 'GLEIF LEI record registeredAs (SIREN) → State company search'), 'query': ras}
    nm = r['name']; res, st = search({'q': nm[:80], 'per_page': 10})
    if res is None: return {'error': str(st), 'query': nm}
    nk = name_key(nm); exact = [x for x in res if name_key(x.get('nom_raison_sociale') or x.get('nom_complet')) == nk]
    near = [(x.get('siren'), x.get('nom_raison_sociale')) for x in res if nk and (name_key(x.get('nom_raison_sociale')).startswith(nk) or nk.startswith(name_key(x.get('nom_raison_sociale'))))][:4]
    if len(exact) == 1 or (exact and all(x['siren'] == exact[0]['siren'] for x in exact)): return {**pack(exact[0], 'name-exact (State company search)'), 'query': nm}
    return {'query': nm, 'n_cands': len(res), 'near': near, 'exact_many': [(x.get('siren'), x.get('nom_raison_sociale')) for x in exact][:4]}
if __name__ == '__main__':
    fn_out = 'raw/siren.jsonl'; done = set()
    if os.path.exists(fn_out):
        for line in open(fn_out, encoding='utf-8'):
            try:
                d = json.loads(line)
                if d.get('siren'): done.add(d['key'])
            except Exception: pass
    todo = [r for r in rows if r['security_type'] == 'Corporate' and r['isin'].startswith('FR') and r['exchange'] + '|' + r['symbol'] not in done]
    print('todo', len(todo), 'done', len(done), flush=True)
    out = open(fn_out, 'a', encoding='utf-8'); n = [0]
    def work(r):
        try: res = match(r)
        except Exception as e: res = {'error': repr(e)[:160]}
        res['key'] = r['exchange'] + '|' + r['symbol']
        with lock:
            out.write(json.dumps(res, ensure_ascii=False) + '\n'); out.flush(); n[0] += 1
            if n[0] % 50 == 0: print(n[0], '/', len(todo), flush=True)
    with ThreadPoolExecutor(max_workers=3) as ex: list(ex.map(work, todo))
    print('DONE', flush=True)
