r"""edgar_cusip.py — DOORS-04 (2026-10-26): which filer a CUSIP belongs to, read on EDGAR (the register of record for SEC filers): EDGAR full-text search for the
CUSIP as written on Schedule 13D/13G cover pages ("CUSIP No."), counted by subject company. ISIN = country + CUSIP + check digit (ISO 6166).
fetch(cusips) -> {cusip: {'subjects': [(name, cik, filings)], 'source_url', 'read_by', 'read_at'}}. Usage: python edgar_cusip.py 384637104 384556106"""
import sys, json, datetime, urllib.request, urllib.parse, collections, time
UA = {'User-Agent': 'Allooloo Technologies Corp. developers@allooloo.ai'}
READ_BY = 'EDGAR full-text search (efts.sec.gov), Schedule 13D/13G cover pages, CUSIP as filed — subject company of each filing'
def isin_of(cc, cusip):
    s = ''.join(str(int(ch, 36)) for ch in (cc + cusip).upper()); d = [int(x) for x in s][::-1]
    t = sum((sum(divmod(x * 2, 10)) if i % 2 == 0 else x) for i, x in enumerate(d)); return cc + cusip.upper() + str((10 - t % 10) % 10)
def fetch(cusips):
    out = {}
    for c in cusips:
        spaced = f'{c[:6]} {c[6:8]} {c[8]}'
        names = collections.Counter(); urls = []
        for q in (c, spaced):
            u = 'https://efts.sec.gov/LATEST/search-index?' + urllib.parse.urlencode({'q': f'"{q}"', 'forms': 'SC 13G,SC 13G/A,SC 13D,SC 13D/A,SCHEDULE 13G,SCHEDULE 13G/A,SCHEDULE 13D,SCHEDULE 13D/A'})
            try: j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40)); urls.append(u)
            except Exception as e: out[c] = {'error': repr(e)[:120]}; continue
            for h in (j.get('hits') or {}).get('hits') or []:
                s = h.get('_source') or {}; dn = s.get('display_names') or []; ciks = s.get('ciks') or []
                # a 13D/13G names the filer and the subject; the subject is the issuer whose CUSIP is on the cover
                for n in dn: names[n] += 1
            time.sleep(0.3)
        out[c] = {'isin_us': isin_of('US', c), 'isin_ca': isin_of('CA', c), 'names': names.most_common(6), 'source_url': urls[0] if urls else None, 'read_by': READ_BY, 'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
    return out
if __name__ == '__main__': print(json.dumps(fetch(sys.argv[1:]), ensure_ascii=False, indent=1))
