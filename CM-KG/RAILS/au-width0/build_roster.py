"""Step 4 — one roster row per listed entity per market from the raw feeds:
  ASX: the directory file (code, name, GICS industry group, listing date) joined to the per-company record (header: sector, industry group, security type,
       status, date listed; key-statistics: ISIN, share description; about: website, contact address, share-registry address, secretaries).
  NSX: the official-list feed (code, name, ISIN, industry, nominated adviser, listed date, summary link).
  TMX Australia: raw/tmxau.json when a browser-session read exists; otherwise no rows (see README / HITL).
Security type from the ASX security type / issue type / share description and the name (ETF, Fund, Trust units, notes → fund / trust / debt)."""
import json, os, re
from collections import Counter
def load(fn, k):
    d = {}
    if os.path.exists(fn):
        for line in open(fn, encoding='utf-8'):
            try:
                x = json.loads(line); d[x[k]] = x
            except Exception: pass
    return d
DIR = json.load(open('raw/asx_directory.json', encoding='utf-8')); CO = load('raw/asx_company.jsonl', 'code'); ANN = load('raw/asx_announcements.jsonl', 'code')
ASX_DIR_SRC = 'https://www.asx.com.au/markets/trade-our-cash-market/directory (directory file asx.api.markitdigital.com/asx-research/1.0/companies/directory/file)'
FUNDY = re.compile(r'\b(ETF|ETFS?|FUND|TRUST|INDEX|PORTFOLIO|UNITS?|NOTES?|BOND|HYBRID|CAPITAL NOTES|ETP|ETC)\b', re.I)
rows = []
def addr(a):
    if not a: return ''
    return ', '.join(v for v in [a.get('address'), a.get('attention')] if v)
for x in DIR:
    code = x['ASX code']; c = CO.get(code, {}); h = c.get('header') or {}; ks = c.get('key_statistics') or {}; ab = c.get('about') or {}; an = ANN.get(code, {})
    st = h.get('securityType'); it = ab.get('issueType') or ''; desc = ks.get('shareDescription') or ''
    if it in ('CS',) and not FUNDY.search(x['Company name']) and not FUNDY.search(desc or ''): stype = 'Corporate'
    elif re.search(r'(?i)\bETF\b|exchange traded', x['Company name'] + ' ' + desc): stype = 'ETF/ETP'
    elif re.search(r'(?i)\btrust\b|\bfund\b|\breit\b', x['Company name']): stype = 'Trust / fund (' + (desc or it or 'by name') + ')'
    elif it: stype = f'{it}' + (f' ({desc})' if desc else '')
    else: stype = 'Corporate' if not FUNDY.search(x['Company name']) else 'Fund (by name)'
    rows.append(dict(exchange='ASX', symbol=code, name=x['Company name'], name_display=ab.get('displayName') or h.get('displayName') or '', security_type=stype, issue_type=it, share_description=desc,
        gics_group=x.get('GICs industry group') or '', sector=h.get('sector') or '', industry_group=h.get('industryGroup') or '', listing_date=(h.get('dateListed') or x.get('Listing date') or ''), status_code=h.get('statusCode') or '',
        isin=ks.get('isin') or '', num_shares=ks.get('numOfShares'), foreign_exempt=ab.get('foreignExempt', ks.get('foreignExempt')), website=ab.get('websiteUrl') or '', contact_address=addr(ab.get('addressContact')), registry_address=addr(ab.get('addressShareRegistry')), registry_phone=(ab.get('addressShareRegistry') or {}).get('phone', ''),
        secretaries='; '.join(s.get('name', '') if isinstance(s, dict) else str(s) for s in (ab.get('secretaries') or [])), indices='; '.join(i.get('name', '') if isinstance(i, dict) else str(i) for i in (ab.get('indices') or [])),
        company_src=c.get('src', ''), header_ok=bool(h), ks_ok=bool(ks), about_ok=bool(ab), ann_12m=an.get('n_12m'), ann_latest=an.get('latest_date', ''), annual_report=an.get('annual_report'), ann_query=an.get('query', ''),
        roster_src=ASX_DIR_SRC, status='Listed'))
if os.path.exists('raw/nsx_list.json'):
    for x in json.load(open('raw/nsx_list.json', encoding='utf-8')):
        nm = re.sub(r'^\[\w+\]\s*', '', x['title']).strip(); code = x.get('issue_code') or re.match(r'\[(\w+)\]', x['title']).group(1)
        rows.append(dict(exchange='NSX', symbol=code, name=nm, name_display=x.get('issue_name', ''), security_type='Corporate' if (x.get('issue_type') or '').endswith('Ordinary') and not FUNDY.search(nm) else (x.get('issue_type') or 'security'), issue_type=x.get('issue_type', ''), share_description=x.get('issue_name', ''),
            gics_group='', sector=x.get('industry') or '', industry_group='', listing_date=x.get('listed_date', ''), status_code='', isin=x.get('isin') or '', num_shares=None, foreign_exempt=None, website='', contact_address='', registry_address='', registry_phone='', secretaries='', indices='',
            company_src=x['link'], header_ok=False, ks_ok=False, about_ok=False, ann_12m=None, ann_latest='', annual_report=None, ann_query='', nominated_adviser=x.get('nominated_adviser', ''), sedol=x.get('sedol', ''),
            roster_src='https://www.nsx.com.au/ftp/rss/nsx_rss_officiallist.xml', status='Listed'))
if os.path.exists('raw/tmxau.json'):
    for x in json.load(open('raw/tmxau.json', encoding='utf-8')).get('rows', []):
        rows.append(dict(exchange='TMX Australia', symbol=x.get('code', ''), name=x.get('name', ''), name_display='', security_type='Corporate', issue_type='', share_description='', gics_group='', sector=x.get('sector', ''), industry_group='', listing_date=x.get('listing_date', ''), status_code='', isin=x.get('isin', ''), num_shares=None, foreign_exempt=None, website=x.get('website', ''), contact_address='', registry_address='', registry_phone='', secretaries='', indices='',
            company_src=x.get('url', ''), header_ok=False, ks_ok=False, about_ok=False, ann_12m=None, ann_latest='', annual_report=None, ann_query='', roster_src='https://www.tmxaustralia.com/listings/companies (read in a browser session)', status='Listed'))
json.dump(rows, open('raw/roster.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print('rows', len(rows), Counter(r['exchange'] for r in rows)); print(Counter((r['exchange'], r['security_type'].split(' (')[0]) for r in rows).most_common(12))
print('ASX with header', sum(1 for r in rows if r['header_ok']), 'with ISIN', sum(1 for r in rows if r['isin']), 'with registry address', sum(1 for r in rows if r['registry_address']), 'with website', sum(1 for r in rows if r['website']), 'with contact address', sum(1 for r in rows if r['contact_address']), 'annual report link', sum(1 for r in rows if r['annual_report']))
