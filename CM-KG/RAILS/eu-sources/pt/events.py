"""Portugal Width 1 events - issuer filings from the CMVM information disclosure system (SDI, Sistema de Difusao de Informacao),
the Portuguese Officially Appointed Mechanism for regulated information (Codigo dos Valores Mobiliarios art. 367).

Server-readable endpoint: the public cmvm.pt site is an OutSystems Reactive app; its own screens call JSON "screen services" with
the anonymous CSRF token that ships in the site's public OutSystems.js. No login, no key, no registration.
  Issuer list ... POST /PInstitucional/screenservices/CMVM_SDI_Emitentes_CW/Emitentes/EmitentesLst/DataActionFetchEmitentes
                  -> [{NOM_ENT, NUM_ENT}] (CMVM entity number per issuer of listed securities)
  Filings ....... POST /PInstitucional/screenservices/CMVM_SDI_Emitentes_CW/Emitentes/InfoDiariaPeriodo/DataActionGetInfoDiaria
                  variables EntityId (0 = all issuers, i.e. per day), StartDate, EndDate, StartIndex, MaxRecords
                  -> [{Id, Table, Date, Time, Desc, Tipo, IsEN}] + CountAll
  File name ..... POST /PInstitucional/screenservices/PInstitucional/ServiceAPIInfoDiariaPeriodoDowFich_PT (_EN2 for English)
                  inputParameters {Id, Tab} -> DownloadFich.NomFich (e.g. FR1292778.pdf). The PDF itself is served only through
                  that server action (no static URL), so "url" is a locator: the CMVM SDI page + #sdi=<Table><Id>.
The API version tokens are read from the live module scripts on every run (they change when CMVM republishes the site).
Each filing appears once per language: the Portuguese line and, where filed, the English line (IsEN), each with its own Id.

fetch(isin_or_issuer, since) -> [{"date", "type", "title", "url", "source", "time", "language", "sdi_id", "sdi_table"}]
  isin_or_issuer: an ISIN from samples/roster-*.json, a CMVM entity number, or an issuer name fragment.
Usage: python events.py [ISIN ...]   (default: EDP, Galp, Jeronimo Martins; 12 months) writes samples/events-<date>.json
"""
import os, re, sys, json, glob, datetime, unicodedata
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = 'https://www.cmvm.pt/PInstitucional/'
PAGE = 'https://www.cmvm.pt/PInstitucional/Single_SDI_StaticContent'  # the SDI screen route (locator base; the document itself needs the server action)
SOURCE = 'CMVM SDI (cmvm.pt information disclosure system, OAM Portugal)'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
VIEW = 'MainFlow.Single_SDI_StaticContent'  # the screen that hosts the SDI blocks (role check passes for anonymous users)


class CMVM:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({'User-Agent': UA, 'Origin': 'https://www.cmvm.pt', 'Referer': BASE})
        mi = self.s.get(BASE + 'moduleservices/moduleinfo', timeout=60).json()['manifest']
        self.ver = mi['versionToken']; self.urls = mi['urlVersions']
        osjs = self._script('/PInstitucional/scripts/OutSystems.js')
        m = re.search(r'AnonymousCSRFToken="([^"]+)"', osjs)
        if not m:
            raise RuntimeError('anonymous CSRF token not found in OutSystems.js')
        self.csrf = m.group(1)  # public constant shipped to every browser; not a credential
        self.api = {}

    def _script(self, path):
        return self.s.get('https://www.cmvm.pt' + path + self.urls[path], timeout=60, headers={'Accept': '*/*'}).text

    def _token(self, script, service):
        if service not in self.api:
            src = self._script(script)
            m = re.search(r'"(screenservices/[^"]*/' + re.escape(service) + r')", "([^"]+)"', src)
            if not m:
                raise RuntimeError(f'{service} not found in {script}')
            self.api[service] = (m.group(1), m.group(2))
        return self.api[service]

    def _post(self, path, token, payload):
        body = {'versionInfo': {'moduleVersion': self.ver, 'apiVersion': token}, 'viewName': VIEW, **payload}
        r = self.s.post(BASE + path, json=body, timeout=120, headers={'X-CSRFToken': self.csrf, 'Content-Type': 'application/json; charset=UTF-8', 'Accept': 'application/json'})
        r.raise_for_status(); j = r.json()
        if j.get('exception'):
            raise RuntimeError(f"CMVM {path.rsplit('/', 1)[-1]}: {j['exception'].get('message')}")
        return j['data']

    def issuers(self):
        path, tok = self._token('/PInstitucional/scripts/CMVM_SDI_Emitentes_CW.Emitentes.EmitentesLst.mvc.js', 'DataActionFetchEmitentes')
        d = self._post(path, tok, {'screenData': {'variables': {'StartIndex': 0, 'MaxRecords': 1000, 'Nome': '', '_nomeInDataFetchStatus': 1}}})
        return [{'name': x['NOM_ENT'], 'entity': x['NUM_ENT']} for x in d['EmitentesLst3']['List']]

    def filings(self, entity, start, end, page=500):
        path, tok = self._token('/PInstitucional/scripts/CMVM_SDI_Emitentes_CW.Emitentes.InfoDiariaPeriodo.mvc.js', 'DataActionGetInfoDiaria')
        v = {'MaxRecords': page, 'StartIndex': 0, 'IsLoading': True, 'InfoDiariaList_Local': {'List': [], 'EmptyListItem': None},
             'LanguageId_Local_Compare': '0', 'StartDate_Local_Compare': '1900-01-01', 'EndDate_Local_Compare': '1900-01-01', 'EntityId_Local_Compare': '0',
             'LanguageId': '0', '_languageIdInDataFetchStatus': 1, 'StartDate': start, '_startDateInDataFetchStatus': 1,
             'EndDate': end, '_endDateInDataFetchStatus': 1, 'EntityId': str(entity), '_entityIdInDataFetchStatus': 1,
             'GetLanguages': {'Language': {'PortugueseId': '0', 'EnglishId': '2'}}}
        out = []
        while True:
            d = self._post(path, tok, {'screenData': {'variables': v}})
            L = d['EmitentesList']['List']; out += L
            if len(L) < page or len(out) >= int(d.get('CountAll') or 0):
                return out
            v['StartIndex'] += page

    def file_name(self, sdi_id, table, english):
        svc = 'ServiceAPIInfoDiariaPeriodoDowFich_EN2' if english else 'ServiceAPIInfoDiariaPeriodoDowFich_PT'
        path, tok = self._token('/PInstitucional/scripts/PInstitucional.controller.js', svc)
        body = {'versionInfo': {'moduleVersion': self.ver, 'apiVersion': tok}, 'viewName': VIEW, 'inputParameters': {'Id': sdi_id, 'Tab': table}}
        r = self.s.post(BASE + path, json=body, timeout=60, headers={'X-CSRFToken': self.csrf, 'Accept': 'application/json'})
        return ((r.json().get('data') or {}).get('DownloadFich') or {}).get('NomFich', '')


def _norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().replace('�', '')
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    drop = {'sa', 's', 'a', 'sgps', 'sociedade', 'gestora', 'de', 'participacoes', 'sociais', 'the', 'company', 'holding', 'nv', 'se', 'plc'}
    return [t for t in s.split() if t not in drop]


def _roster():
    files = sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')))
    return {r['isin']: r for r in json.load(open(files[-1], encoding='utf-8'))['rows']} if files else {}


def resolve(cm, key):
    """ISIN / entity number / name fragment -> (entity number, CMVM issuer name, matched-by)."""
    iss = cm.issuers()
    if re.fullmatch(r'\d+', key):
        hit = [x for x in iss if x['entity'] == key]
        return (key, hit[0]['name'] if hit else '', 'entity number')
    names = [key]
    if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}\d', key):
        names = [n for n in [_roster().get(key, {}).get('name', '')] if n]
        try:  # the Euronext list name (e.g. "JERONIMO MARTINS" where FIRDS has "J.MARTINS,SGPS")
            import roster as _r
            names += [x['name'] for x in _r.euronext_list() if x['isin'] == key]
        except Exception:
            pass
        if not names:
            raise LookupError(f'{key}: ISIN not in the roster sample; pass a CMVM entity number or a name')
    best, score, used = None, 0, ''
    for name in names:
        want = _norm(name)
        for x in iss:
            have = _norm(x['name'])
            if not have or not want:
                continue
            first = have[0].startswith(want[0]) or want[0].startswith(have[0])
            sc = len(set(want) & set(have)) + (2 if first else 0) - 0.1 * abs(len(have) - len(want))
            if first and sc > score:
                best, score, used = x, sc, name
    if best is None:
        raise LookupError(f'{key}: no CMVM issuer matches {names}')
    return best['entity'], best['name'], f'name match on "{used}"'


def fetch(isin_or_issuer, since, cm=None, until=None, with_files=False):
    cm = cm or CMVM()
    ent, cname, how = resolve(cm, isin_or_issuer)
    since = since if isinstance(since, str) else since.isoformat()
    until = until or datetime.date.today().isoformat()
    rows = []
    for x in cm.filings(ent, since, until):
        ev = {'date': x['Date'], 'type': x['Tipo'], 'title': x['Desc'],
              'url': f"{PAGE}#sdi={x['Table']}{x['Id']}", 'source': SOURCE, 'time': x['Time'],
              'language': 'en' if x.get('IsEN') else 'pt', 'sdi_id': x['Id'], 'sdi_table': x['Table'],
              'issuer_entity': ent, 'issuer_name_cmvm': cname}
        if with_files:
            ev['file_name'] = cm.file_name(x['Id'], x['Table'], bool(x.get('IsEN')))
        rows.append(ev)
    return rows


if __name__ == '__main__':
    keys = [a for a in sys.argv[1:] if not a.startswith('--')] or ['PTEDP0AM0009', 'PTGAL0AM0009', 'PTJMT0AE0001']
    today = datetime.datetime.now(datetime.timezone.utc).date()
    since = (today - datetime.timedelta(days=365)).isoformat()
    cm = CMVM(); out = {'source': SOURCE, 'endpoint': BASE + 'screenservices/CMVM_SDI_Emitentes_CW/Emitentes/InfoDiariaPeriodo/DataActionGetInfoDiaria',
                        'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'since': since, 'issuers': {}}
    for k in keys:
        ent, cname, how = resolve(cm, k)
        ev = fetch(k, since, cm=cm, until=today.isoformat())
        # one file name per issuer as a proof that the document locator resolves
        if ev:
            ev[0]['file_name'] = cm.file_name(ev[0]['sdi_id'], ev[0]['sdi_table'], ev[0]['language'] == 'en')
        types = {}
        for e in ev:
            types[e['type']] = types.get(e['type'], 0) + 1
        out['issuers'][k] = {'cmvm_entity': ent, 'cmvm_name': cname, 'matched_by': how, 'count': len(ev),
                             'count_pt': sum(1 for e in ev if e['language'] == 'pt'), 'count_en': sum(1 for e in ev if e['language'] == 'en'),
                             'types': dict(sorted(types.items(), key=lambda t: -t[1])), 'events': ev}
        print(k, ent, cname.encode('ascii', 'replace').decode(), 'events', len(ev), flush=True)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    fn = os.path.join(HERE, 'samples', f'events-{today.isoformat()}.json')
    json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', fn)
