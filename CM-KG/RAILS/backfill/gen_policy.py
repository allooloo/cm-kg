r"""gen_policy.py — BACKFILL-01 B-2 (DAY ORDER 7, 2026-10-25): writes policy.json, the backfill policy line of every market (archive, base URL, earliest
reachable date, licence note, reader engine, adapter, wave, pace). The archives are the order's B-3 table; the base URL is the archive the market's live rail
already reads (its source module), so the same stack points backward. earliest_reachable stays null until the rail has read it (B-4: declared, never
assumed). One-shot generator; policy.json is the policy of record afterwards (a new market adds its line there). .pre copy beside on a re-run."""
import os, json, shutil, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'policy.json')
W1 = lambda steps, env=None: {'adapter': 'width1-window', 'steps': steps, 'env': env or {}}
EUV = lambda: {'adapter': 'eu-node-events'}
NONE = {'adapter': 'none', 'why': 'no pull of its own — its issuers\' rows live in the listing market, as today (B-3)'}
K, KEY = 'keyless', 'key (AGENT KEYS, by file name)'
M = [  # cc, wave, archive (B-3), base_url (the live rail's source), licence note, reader, adapter line, pace (requests per second, the archive's own limit or less)
 ('ca', 1, 'SEDAR+', 'https://www.sedarplus.ca/', 'SEDAR+ document search sits behind a Radware bot wall with hCaptcha (read 2026-10-25): never bypassed. The same stack the live record reads is pointed backward: TSX Venture bulletins (TMX), CSE bulletins API, Cision and PR Newswire release archives; Newsfile shows its latest 20 per company.', K,
  W1(['tsxv_bulletins.py', 'cse_bulletins.py', 'wire_pages.py'], {'SKIP_WIRE': 'Newsfile', 'THREADS': '4', 'DELAY': '0.5'}), 2),
 ('us', 2, 'EDGAR', 'https://data.sec.gov/submissions/', 'SEC EDGAR: public domain; fair access 10 requests per second with a declared user agent', K, {'adapter': 'edgar'}, 8),
 ('uk', 2, 'NSM', 'https://www.investegate.co.uk/', 'FCA National Storage Mechanism is the archive of record; the live rail reads RNS through Investegate and Companies House filings', K, W1(['investegate.py', 'ch_filings.py']), 2),
 ('hk', 2, 'HKEXnews', 'https://www1.hkexnews.hk/search/titlesearch.xhtml', 'HKEXnews title search, English-language filings', K, W1(['hkexnews_search.py']), 2),
 ('kr', 2, 'DART', 'https://opendart.fss.or.kr/', 'DART Open API, key by file name (dart.txt); 10,000 calls a day', KEY, W1(['dart_events.py']), 2),
 ('sg', 2, 'SGXNet', 'https://api.sgx.com/', 'SGXNet company announcements; ACRA events', K, W1(['sgxnet_search.py', 'acra_events.py']), 2),
 ('tw', 2, 'MOPS', 'https://mops.twse.com.tw/mops/', 'MOPS material information (Market Observation Post System)', K, EUV(), 1),
 ('in', 2, 'BSE/NSE', 'https://www.nseindia.com/companies-listing/corporate-filings-announcements', 'NSE corporate announcements (BSE as fallback); both refuse Azure egress (Akamai) — the laptop reads them', K, EUV(), 1),
 ('br', 2, 'CVM', 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/', 'CVM open data (IPE/ITR/DFP) yearly files; no English labels published', K, EUV(), 2),
 ('mx', 2, 'BMV/Emisnet', 'https://www.bmv.com.mx/es/emisoras/eventosrelevantes/', 'BMV relevant events (Emisnet); BIVA information bank as fallback', K, EUV(), 1),
 ('es', 3, 'CNMV', 'https://www.cnmv.es/portal/Informacion-Privilegiada/Resultado-IP', 'CNMV inside information and other relevant information', K, EUV(), 1),
 ('fr', 3, 'AMF/BALO', 'https://bdif.amf-france.org/', 'AMF BDIF (regulated information); BALO for legal notices', K, W1(['bdif_events.py']), 2),
 ('it', 3, 'eMarket Storage', 'https://www.emarketstorage.it/it/comunicati-finanziari', 'eMarket Storage (Teleborsa) regulated information', K, EUV(), 1),
 ('pl', 3, 'ESPI', 'https://www.gpw.pl/espi-ebi-reports', 'ESPI/EBI current reports (GPW)', K, EUV(), 1),
 ('pt', 3, 'CMVM', 'https://www.cmvm.pt/PInstitucional/', 'CMVM information disclosure system', K, EUV(), 1),
 ('lu', 3, 'LuxSE OAM', 'https://www.luxse.com/issuer-services-overview/oam', 'LuxSE Officially Appointed Mechanism', K, EUV(), 1),
 ('de', 3, 'Unternehmensregister', 'https://www.unternehmensregister.de/', 'Unternehmensregister is the archive of record; the live rail reads EQS ad hoc and directors\' dealings', K, W1(['eqs_search.py']), 1),
 ('no', 3, 'Newsweb', 'https://api3.oslo.oslobors.no/v1/newsreader/list', 'Oslo Bors Newsweb', K, EUV(), 2),
 ('ie', 3, 'Euronext Dublin', 'https://direct.euronext.com/api/PublicAnnouncements/OAMs', 'Euronext Dublin OAM public announcements', K, EUV(), 1),
 ('gr', 3, 'Athens Exchange (HCMC OAM)', 'https://athens.euronext.com/', 'Greece is on the roster but not in the B-3 table: CC wrote this line from the archive the live Greek rail reads (Euronext Athens announcements; HCMC is the OAM of record), last in wave 3 — the CEO confirms or moves it', K, EUV(), 1),
 ('au', 4, 'ASX', 'https://www.asx.com.au/markets/trade-our-cash-market/announcements', 'ASX announcements: the free window is limited (B-4); ASIC and NSX events beside', K, W1(['asx_events.py', 'asic_events.py', 'nsx_events.py']), 2),
 ('ae', 4, 'ADX/DFM', 'https://www.dfm.ae/the-exchange/news-disclosures/disclosures', 'DFM disclosures (English); ADX needs a key (adx-Gateway-APIKey, CEO hand)', K, EUV(), 1),
 ('nl', 4, 'AFM', 'https://www.afm.nl/en/sector/registers', 'AFM registers (regulated information)', K, W1(['afm_events.py']), 2),
 ('be', 4, 'FSMA', 'https://webapi.fsma.be/api/v1/en/stori/result', 'FSMA STORI', K, EUV(), 1),
 ('at', 4, 'OeKB', 'https://issuerinfo.oekb.at/', 'OeKB issuer information (OAM)', K, EUV(), 1),
 ('se', 4, 'FI', 'https://api.news.eu.nasdaq.com/news/query.action', 'Finansinspektionen is the OAM of record; the live rail reads Nasdaq Nordic company news', K, EUV(), 2),
 ('dk', 4, 'the Nordic registers', 'https://api.news.eu.nasdaq.com/news/query.action', 'Nasdaq Nordic company news (Copenhagen)', K, EUV(), 2),
 ('fi', 4, 'the Nordic registers', 'https://api.news.eu.nasdaq.com/news/query.action', 'Nasdaq Nordic company news (Helsinki)', K, EUV(), 2),
 ('cz', 4, 'Czech National Bank', 'https://oam.cnb.cz/sipresextdad/SIPRESWEB.WEB21.START_INPUT_OAM', 'CNB OAM (regulated information)', K, EUV(), 1),
 ('ch', 5, 'SIX', 'https://www.six-group.com/', 'SIX ad hoc notices (pre-2021 depth limited, B-4); EQS and SHAB beside', K, W1(['eqs_search.py', 'shab_events.py']), 1),
 ('jp', 5, 'EDINET', 'https://api.edinet-fsa.go.jp/api/v2/', 'EDINET API v2, key by file name (edinet.txt); TDnet timely disclosures keep about a month free (B-4); Gemini reads Japanese', KEY, W1(['edinet_events.py']), 2),
 ('ky', 0, 'none', None, 'Cayman Islands: no pull of its own (B-3)', None, NONE, 0),
 ('bm', 0, 'none', None, 'Bermuda: no pull of its own (B-3)', None, NONE, 0),
 ('je', 0, 'none', None, 'Jersey: no pull of its own (B-3)', None, NONE, 0),
]
pol = {'policy': 'BACKFILL-01 backfill policy of record (DAY ORDER 7, 2026-10-25)', 'epoch': '2021-01-01',
       'order': [c for c, *_ in M if _[0] > 0], 'engine_roles': 'Gemini reads Japanese; machine-English is never a source; Perplexity and Tavily are a search layer only where an archive has no index (no backfill line uses them)',
       'not_on_roster': {'sa': 'Saudi Arabia — not on the roster; nothing (B-3)'}, 'markets': {}}
for cc, wave, arch, url, note, reader, ad, rps in M:
    pol['markets'][cc] = {'wave': wave, 'archive': arch, 'base_url': url, 'earliest_reachable': None, 'licence_note': note, 'reader': reader, **ad, 'pace': {'rps': rps}}
if os.path.exists(P): shutil.copy2(P, P + '.pre-' + datetime.datetime.now().strftime('%Y%m%d%H%M'))
json.dump(pol, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('policy lines:', len(pol['markets']), '· order:', ' '.join(pol['order']))
