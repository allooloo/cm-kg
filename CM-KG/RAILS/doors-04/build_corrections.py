r"""DOORS-04 — writes RAILS\door\isin_corrections.json (the corrections of record the nightly fold applies) from the register reads:
  jp  JPX Listed Company Search, both codes of every pair (isin-fill\jp_isin.py) — the record whose ISIN JPX gives to the other code is corrected to its own
  us  EDGAR (isin-fill\edgar_cusip.py + the subject's own 13G CUSIP) — the record whose ISIN EDGAR gives to another filer is corrected
  ca  ETF Facts as filed on SEDAR+ (manager-hosted copy), CSE listing page, TSXV bulletin, EDGAR — from ca-reads.json beside (ticker -> cusip, document)
A .pre copy of the corrections file is kept on every write. Usage: python -X utf8 -I build_corrections.py jp|us|ca"""
import json, os, sys, glob, shutil, datetime, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = r'C:\ALLOOLOO\CM-KG\RAILS\door\isin_corrections.json'
def mod(p, n): s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
EC = mod(r'C:\ALLOOLOO\CM-KG\RAILS\isin-fill\edgar_cusip.py', 'edgar_cusip')
G = json.load(open(sorted(glob.glob(os.path.join(HERE, 'groups-*.json')))[-1], encoding='utf-8'))
C = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
if os.path.exists(OUT): shutil.copy2(OUT, OUT + '.pre-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
which = sys.argv[1]; hand = []
if which == 'jp':
    JP = mod(r'C:\ALLOOLOO\CM-KG\RAILS\isin-fill\jp_isin.py', 'jp_isin')
    for g, recs in G.items():
        if not g.startswith('jp:'): continue
        isin = g.split(':')[1]; codes = {k: k.split('/')[2] for k in recs}; R = JP.fetch(list(codes.values()))
        owners = [k for k in recs if R[codes[k]].get('isin') == isin]
        if len(owners) != 1 or any('error' in R[c] for c in codes.values()): hand.append((g, 'JPX did not settle it', {c: R[c] for c in codes.values()})); continue
        for k in recs:
            if k in owners: continue
            r = R[codes[k]]; C.setdefault('jp-cm-kg', {})[k] = {'isin': r['isin'], 'was': isin, 'source_url': r['source_url'], 'read_by': r['read_by'], 'read_at': r['read_at'],
                                                                 'note': f"JPX gives {isin} to {owners[0].split('/', 1)[1]} ({recs[owners[0]]['name']}); this issue's own ISIN read at JPX. The LEI on this record came by the same name match and is flagged for re-read."}
elif which == 'us':
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    C.setdefault('us-cm-kg', {})['us-cm-kg/NYSE/GHC'] = {'isin': EC.isin_of('US', '384637104'), 'was': 'US3845561063', 'read_at': now, 'read_by': EC.READ_BY + ' · ISIN = US + CUSIP + check digit (ISO 6166)',
        'source_url': 'https://efts.sec.gov/LATEST/search-index?q=%22384637104%22 (Schedule 13D/13G covers: subject Graham Holdings Co, CIK 0000104889)',
        'note': 'EDGAR gives CUSIP 384556106 (US3845561063) to GRAHAM CORP (GHM, CIK 716314) and 384637104 to Graham Holdings Co (GHC, CIK 104889)'}
    C['us-cm-kg']['us-cm-kg/NASDAQ/SATS'] = {'isin': EC.isin_of('US', '862945102'), 'was': 'US2787681061', 'read_at': now, 'read_by': 'EDGAR Schedule 13G/A (structured), issuerCusip of the subject company · ISIN = US + CUSIP + check digit (ISO 6166)',
        'source_url': 'https://www.sec.gov/Archives/edgar/data/1920406/000121390025087870/primary_doc.xml (issuer STRIVE, INC., CIK 0001920406, issuerCusip 862945102)',
        'note': 'EDGAR gives CUSIP 278768106 (US2787681061) to EchoStar Corp (CIK 1415404, the NASDAQ/ECHO record); Strive, Inc. files under its own CUSIP 862945102'}
elif which == 'ca':
    reads = json.load(open(os.path.join(HERE, 'ca-reads.json'), encoding='utf-8'))   # {ticker: {cusip, document, ...}} from the ETF Facts / CSE / TSXV reads
    owners = json.load(open(os.path.join(HERE, 'ca-owners.json'), encoding='utf-8'))  # {isin: {owner: cmr or null, by: '...', source_url: '...'}} from EDGAR
    for g, recs in G.items():
        if not g.startswith('ca:'): continue
        isin = g.split(':')[1]; ow = owners.get(isin, {}).get('owner')
        if not ow:   # no EDGAR owner on the group: the record whose own register read gives this ISIN owns it
            own = [k for k in recs if (reads.get(k.split('/')[2]) or {}).get('cusip') and EC.isin_of('CA', reads[k.split('/')[2]]['cusip']) == isin]
            if len(own) == 1: ow = own[0]; owners[isin] = {'owner': ow, 'owner_name': recs[ow]['name'], 'by': 'its own register read (' + reads[ow.split('/')[2]]['document'] + ')', 'source_url': reads[ow.split('/')[2]]['document'], 'read_at': reads[ow.split('/')[2]].get('read_at') or datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
        for k in recs:
            t = k.split('/')[2]; rd = reads.get(t) or {}
            if k == ow and 'ruling' not in (rd.get('read_by') or ''): continue
            if rd.get('cusip'):
                new = EC.isin_of('CA', rd['cusip'])
                ruled = 'ruling' in (rd.get('read_by') or '')   # DOORS-05: a manager-published value is written as filled, the owner's too (its source becomes the manager page)
                if new == isin and not ruled: continue   # the register gives this record this ISIN: it is the owner
                C.setdefault('ca-cm-kg', {})[k] = {'isin': new, 'was': isin, **({'state': 'filled'} if ruled else {}), 'source_url': rd['document'], 'read_by': rd.get('read_by') or 'ETF Facts as filed on SEDAR+ (manager-hosted copy), CUSIP as printed · ISIN = CA + CUSIP + check digit (ISO 6166)',
                                                   'read_at': rd.get('read_at') or datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'note': f"the register prints CUSIP {rd['cusip']} for {t}; {isin} " + (f"belongs to {owners[isin]['owner_name']} ({owners[isin]['by']})" if owners.get(isin, {}).get('owner_name') else 'is not this issue’s')}
            elif ow or owners.get(isin, {}).get('owner_name'):   # the register proves the value is another issuer's, and prints none for this one
                C.setdefault('ca-cm-kg', {})[k] = {'isin': None, 'was': isin, 'source_url': owners[isin]['source_url'], 'read_by': owners[isin]['by'], 'read_at': owners[isin]['read_at'],
                                                   'note': f"{isin} belongs to {owners[isin]['owner_name']} by its register; no register of record printed this issue's own CUSIP ({rd.get('note') or 'not found'})"}
            else: hand.append((g, k, rd.get('note') or 'no register read'))
json.dump(C, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(which, 'corrections now', {n: len(v) for n, v in C.items()}); [print('HAND', h) for h in hand]
