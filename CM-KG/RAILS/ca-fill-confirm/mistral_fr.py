"""Pass 2.5 — Mistral (mistral-small-latest) reads French-language releases (Québec issuers, French wires) and extracts the same
fields as the ChatGPT and Gemini passes from the French text: period_end, statement_date, auditor_named, going_concern, and any
stated meeting or record date. Label: 'read by Mistral (fr)'. A release is French when its title or body reads as French."""
import hashlib, re
from fc_common import *
FR_T = re.compile(r"\b(annonce|résultats|trimestre|exercice|assemblée|actionnaires|financiers|société|dividende|clôture|conseil d'administration|nomination|acquisition de|émission|déclare|publie|dépôt|états financiers)\b", re.I)
def body_of(url):
    fn = 'raw/bodies/' + hashlib.sha1(url.encode()).hexdigest() + '.txt'
    return open(fn, encoding='utf-8').read() if os.path.exists(fn) else ''
def is_french(title, body):
    t = (title + ' ' + body[:1500]).lower()
    fr = len(re.findall(r"\b(le|la|les|des|du|de la|et|pour|avec|dans|une|un|est|sont|que|qui|société|annonce|résultats)\b", t))
    en = len(re.findall(r"\b(the|and|of|for|with|in|is|are|that|which|announces|results|company)\b", t))
    return bool(FR_T.search(title)) or (fr > en and fr >= 6)
def fetch(e):
    b = body_of(e['url'])
    prompt = (f"Émetteur : {e['issuer']} ({e['exchange']} : {e['ticker']}). Titre du communiqué : {e['title']}\n\nTEXTE DU COMMUNIQUÉ :\n{b[:14000] if b else '(texte non récupéré ; titre seulement)'}\n\n"
              "Extrais uniquement ce que le texte énonce (jamais d'inférence ; chaîne vide sinon). Réponds en JSON strict : "
              "{\"period_end\": \"AAAA-MM-JJ ou vide\", \"statement_date\": \"AAAA-MM-JJ ou vide\", \"auditor_named\": \"cabinet d'audit nommé ou vide\", \"going_concern\": \"yes|no\", "
              "\"meeting_date\": \"AAAA-MM-JJ ou vide\", \"record_date\": \"AAAA-MM-JJ ou vide\", \"evidence\": \"phrase(s) exacte(s), 400 caractères max\"}")
    res = mistral(prompt)
    j = jparse(res.get('text', '')) or {}
    return {'url': e['url'], 'has_body': bool(b), **{k: j.get(k, '') for k in ('period_end', 'statement_date', 'auditor_named', 'going_concern', 'meeting_date', 'record_date', 'evidence')}, 'usage': res.get('usage'), 'error': res.get('error')}
if __name__ == '__main__':
    seen = set(); targets = []
    for e in events():
        if e['url'] in seen: continue
        if is_french(e['title'], body_of(e['url'])): seen.add(e['url']); targets.append(e)
    print('French releases', len(targets), 'with body', sum(1 for e in targets if body_of(e['url'])), flush=True)
    resume('mistral_fr', fetch, targets, threads=int(E.get('THREADS', '4')), keyf=lambda e: e['url'])
