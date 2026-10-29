"""GR Width 1 events: issuer announcements (regulated information) as published on Euronext Athens.

Source  : https://athens.euronext.com/{el|en}/more-options/announcements-companies  (Drupal view, server-rendered HTML)
          Query string: field_mig_category_2=<issuer id>  field_mig_category_1=<category id>  page=<n> (12 rows per page,
          newest first). Issuer ids come from the view's own issuer radio list (fetched live). No login, no key.
          Euronext Athens (ex-ATHEX) publishes the regulated information its issuers file under the Transparency Directive;
          the Hellenic Capital Market Commission (HCMC, www.hcmc.gr) supervises but does not run a separate
          server-readable filings store (checked 2026-10-24: none found).
type    : the store's own category ('Prospectuses and Reports', 'General Assembly', 'Distributions', ...). A filing the
          view lists for the issuer but under none of the ten categories is typed 'Announcement (uncategorised)'.
title   : as filed. lang='el' (default) gives the Greek original; lang='en' gives the English listing, where Greek-only
          filings read 'Announcement NNNN/YYYY (no English translation available)'.

fetch(isin_or_issuer, since)  isin_or_issuer = ISIN (resolved through the latest samples/roster-*.json name, then fuzzy-
matched to the exchange's issuer list), an exchange issuer id (digits), or an issuer name.
"""
import datetime as dt, functools, glob, html, json, os, re, sys, time, unicodedata
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
BASE = 'https://athens.euronext.com'
VIEW = BASE + '/{lang}/more-options/announcements-companies'
CATEGORIES = {'2': 'Prospectuses and Reports', '3': 'Presentations', '4': 'General Assembly', '5': 'Financial Calendar',
              '6': 'Distributions', '7': 'Corporate Actions', '8': 'Board & Management Changes',
              '9': 'Acquisition or disposal of Own Shares', '10': 'Notifications of Transactions', '11': 'Announcements'}
ROW = re.compile(r'views-field-field-issuer">(.*?)</td>.*?<a href="([^"]+)"[^>]*>(.*?)</a>.*?datetime="([^"]+)"', re.S)
_S = requests.Session(); _S.headers.update(UA)


def _get(url, params=None, tries=4):
    for i in range(tries):
        try:
            r = _S.get(url, params=params, timeout=90)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(3 * (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(3 * (i + 1))
    raise RuntimeError(f'unreachable: {url} {params}')


def _norm(s):
    s = unicodedata.normalize('NFKD', html.unescape(s or '')).encode('ascii', 'ignore').decode().upper()
    s = re.sub(r'[^A-Z0-9 ]', ' ', s)
    stop = {'S', 'A', 'SA', 'THE', 'COMPANY', 'CO', 'HOLDINGS', 'HOLDING', 'INC', 'PLC', 'AG', 'NV', 'SE', 'LTD', 'CORP', 'GROUP',
            'SOCIETE', 'ANONYME', 'ANONYMOUS', 'OF', 'AND', 'INDUSTRIAL', 'COMMERCIAL', 'SINGLE', 'MEMBER'}
    return {w for w in s.split() if w not in stop and len(w) > 1}


@functools.lru_cache(maxsize=1)
def issuers():
    """{issuer_id: label} from the exchange's own issuer filter (English labels)."""
    t = _get(VIEW.format(lang='en')).text
    out = {}
    for x in re.findall(r'<input[^>]*name="field_mig_category_2"[^>]*>', t):
        v, i = re.search(r'value="([^"]*)"', x).group(1), re.search(r'id="([^"]+)"', x).group(1)
        lab = re.search(r'<label[^>]*for="%s"[^>]*>(.*?)</label>' % re.escape(i), t, re.S)
        if v != 'All' and lab:
            out[v] = html.unescape(re.sub(r'<[^>]+>', '', lab.group(1))).replace('\xa0', ' ').strip()
    return out


# FIRDS names that do not share words with the exchange's issuer label (ticker -> exchange label)
OVERRIDES = {'ASCO': 'AS COMPANY S.A.', 'HAIDE': 'XAIDEMENOS S.A.', 'PPA': 'PIRAEUS PORT AUTHORITY SA',
             'PPC': 'PUBLIC POWER CORPORATION SA', 'OLTH': 'THESSALONIKI PORT AUTHORITY S.A.',
             'EYAPS': 'THESSALONIKI WATER AND SEWAGE COMPANY SA', 'MTLN': 'METLEN ENERGY & METALS PLC',
             'HTO': 'HELLENIC TELECOM. ORG.', 'EYDAP': 'ATHENS WATER SUPPLY & SEWAGE Co.'}


def _roster_row(isin):
    for p in sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')), reverse=True):
        for r in json.load(open(p, encoding='utf-8'))['rows']:
            if r['isin'] == isin:
                return r
    return None


def _n(s):
    s = re.sub(r'\((CR|CB|PR)\)', '', s or '').replace('NAT.', 'NATIONAL ').replace('TELECOM.', 'TELECOMMUNICATIONS ')
    s = s.replace('IND.', 'INDUSTRY ').replace('INTER/NAL', 'INTERNATIONAL')
    return _norm(s)


def resolve(isin_or_issuer):
    """-> (issuer_id, label, how). Name match = share of the shorter name's words found in the other."""
    q = str(isin_or_issuer).strip()
    iss = issuers()
    if q.isdigit() and q in iss:
        return q, iss[q], 'issuer id'
    name, how = q, 'name'
    if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}[0-9]', q):
        row = _roster_row(q)
        if not row:
            raise LookupError(f'{q}: not in the latest roster sample; run roster.py first or pass an issuer name/id')
        name, how = row['name'], f'ISIN -> FIRDS name "{row["name"]}"'
        lab = OVERRIDES.get(row.get('ticker') or '')
        for k, v in iss.items():
            if lab and v == lab:
                return k, v, how + f' -> exchange issuer "{v}" (id {k}, override by ticker {row["ticker"]})'
    want = _n(name)
    def sc(v):
        got = _n(v)
        return (len(want & got) / max(1, min(len(want), len(got))), len(want & got) / max(1, len(want | got)))
    ranked = sorted(iss.items(), key=lambda kv: sc(kv[1]), reverse=True)
    best, score = ranked[0], sc(ranked[0][1])
    if score[0] < 0.6 or (len(ranked) > 1 and sc(ranked[1][1]) == score):
        raise LookupError(f'{q}: no confident issuer match (best "{best[1]}" score {score[0]:.2f}); pass the exchange issuer id')
    return best[0], best[1], how + f' -> exchange issuer "{best[1]}" (id {best[0]}, match {score[0]:.2f})'


def _list(issuer_id, since, lang, category=None, max_pages=60):
    out = []
    for page in range(max_pages):
        p = {'field_mig_category_2': issuer_id, 'page': page}
        if category:
            p['field_mig_category_1'] = category
        rows = ROW.findall(_get(VIEW.format(lang=lang), p).text)
        if not rows:
            break
        stop = False
        for _, href, title, when in rows:
            d = when[:10]
            if d < since:
                stop = True; continue
            out.append({'date': when, 'title': html.unescape(re.sub(r'<[^>]+>', '', title)).strip(), 'url': BASE + href})
        if stop or len(rows) < 12:
            break
    return out


def fetch(isin_or_issuer, since=None, lang='el'):
    since = since or (dt.date.today() - dt.timedelta(days=365)).isoformat()
    iid, label, how = resolve(isin_or_issuer)
    typed = {}
    for cid, cname in CATEGORIES.items():
        for e in _list(iid, since, lang, cid):
            typed.setdefault(e['url'], cname)
    events = []
    for e in _list(iid, since, lang):
        events.append({'date': e['date'], 'type': typed.get(e['url'], 'Announcement (uncategorised)'), 'title': e['title'],
                       'url': e['url'], 'source': 'Euronext Athens issuer announcements', 'issuer': label, 'resolved_by': how})
    return events


if __name__ == '__main__':
    since = (dt.date.today() - dt.timedelta(days=365)).isoformat()
    tests = sys.argv[1:] or ['GRS003003035', 'GRS830003000', 'GRS434003000']  # National Bank of Greece, Alpha Bank, PPC
    out = {'source_url': VIEW.format(lang='el'), 'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'since': since, 'issuers': {}}
    for t in tests:
        try:
            ev = fetch(t, since)
            out['issuers'][t] = {'count': len(ev), 'resolved_by': ev[0]['resolved_by'] if ev else None, 'events': ev}
            print(t, len(ev), ev[0]['resolved_by'] if ev else '', flush=True)
        except Exception as e:
            out['issuers'][t] = {'error': str(e)}; print(t, 'ERROR', e, flush=True)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    p = os.path.join(HERE, 'samples', f'events-{dt.datetime.now(dt.timezone.utc).date().isoformat()}.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', p)
