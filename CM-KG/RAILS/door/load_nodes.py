r"""Node-generic loader for the doors (replaces CM-KG\RAILS\ca-door\load.py from ORDER-010). Reads the CONFIRMED outputs of every live node:
   CM-KG\ISSUERS\<cc>-issuers.xlsx            -> one CMR v0 per row
   CM-KG\DISCLOSURE\events\<cc>-events.jsonl  -> events per issuer, newest first
and writes the door's data files under CM-KG\DOOR\data\ (Workers Static Assets; D1 and KV are refused by the account token):
   records/<node>/<EXCHANGE>/<TICKER>.json   events/<node>/<EXCHANGE>/<TICKER>.json   index.json (all nodes)   facts.json   nodes.json
Idempotent on (node, exchange, ticker): every file is rewritten from the workbook. Re-run after every weekly sweep, then `wrangler deploy` in CM-KG\DOOR.
Usage: python load_nodes.py [ca uk ...]   (default: every node with a workbook present). AS_OF_<CC> and CMR_VERSION_<CC> env vars per node."""
import openpyxl, json, os, re, datetime, sys, shutil
ROOT = r'C:\ALLOOLOO'; OUT = os.path.join(ROOT, r'CM-KG\DOOR\data')
NODES = [('ca', 'Canada'), ('uk', 'United Kingdom'), ('au', 'Australia'), ('sg', 'Singapore'), ('ch', 'Switzerland'), ('de', 'Germany'), ('fr', 'France'), ('nl', 'Netherlands'), ('hk', 'Hong Kong'), ('jp', 'Japan'), ('kr', 'South Korea'), ('us', 'United States')]
def slug_ticker(t): return re.sub(r'[^A-Za-z0-9.\-]', '_', str(t))
def gaps_of(text):
    out = {}
    for part in (text or '').split('; '):
        if ':' in part:
            f, why = part.split(':', 1); out[f.strip()] = why.strip()
    return out
def nkey(s): return re.sub(r'[^a-z0-9]+', ' ', str(s).lower().replace('&', ' and ')).strip()
# ---- per-node column maps: cmr field -> (value col, source col, read-by col, state col, gaps label)
CA = {'tabs': {'TSX': 'TSX', 'TSXV': 'TSXV', 'CSE': 'CSE', 'Cboe Canada': 'CBOE-CANADA'}, 'ticker': 'Ticker', 'name': 'Legal name', 'default_as_of': '2026-09-10',
      'fields': {'name': ('Legal name', 'Roster source', 'Roster read by', None, None), 'ticker': ('Ticker', 'Roster source', 'Roster read by', None, None), 'exchange': ('Exchange', 'Roster source', 'Roster read by', None, None),
                 'security_type': ('Security type', 'Sector source', 'Sector read by', None, None), 'isin': ('ISIN', 'ISIN source', 'ISIN read by', 'ISIN state', 'ISIN'), 'lei': ('LEI', 'LEI source', 'LEI read by', 'LEI state', 'LEI'),
                 'sector': ('Sector', 'Sector source', 'Sector read by', None, 'Sector'), 'jurisdiction': ('Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Incorporation jurisdiction state', 'Incorporation jurisdiction'),
                 'transfer_agent': ('Transfer agent', 'Transfer agent source', 'Transfer agent read by', 'Transfer agent state', 'Transfer agent'), 'auditor': ('Auditor', 'Auditor source', 'Auditor read by', 'Auditor state', 'Auditor'),
                 'newswire': ('Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire of habit state', 'Newswire of habit'), 'hq_city': ('HQ city', 'HQ source', 'HQ read by', None, 'HQ city'), 'hq_region': ('HQ province/state', 'HQ source', 'HQ read by', None, 'HQ province/state'),
                 'tier': ('Listing tier', 'Roster source', 'Roster read by', None, 'Listing tier'), 'sedar_profile': ('SEDAR+ profile link', 'SEDAR+ source', 'SEDAR+ read by', None, 'SEDAR+ profile link'), 'sedi_link': ('SEDI link (unverified — HTTP 403 on fetch)', None, 'SEDI read by', None, 'SEDI link')},
      'second': {'isin': 'ISIN', 'lei': 'LEI', 'transfer_agent': 'Transfer agent', 'auditor': 'Auditor', 'newswire': 'Newswire of habit', 'jurisdiction': 'Incorporation jurisdiction'}, 'prefixes': ['TSX', 'TSXV', 'CSE', 'CBOE-CANADA']}
UK = {'tabs': {'LSE Main Market': 'LSE', 'AIM': 'AIM', 'Aquis Stock Exchange': 'AQSE'}, 'ticker': 'Ticker (TIDM)', 'name': 'Legal name', 'default_as_of': '2026-09-11',
      'fields': {'name': ('Legal name', 'Roster source', 'Roster read by', None, None), 'ticker': ('Ticker (TIDM)', 'Roster source', 'Roster read by', None, None), 'exchange': ('Exchange', 'Roster source', 'Roster read by', None, None),
                 'market_segment': ('Market segment', 'Roster source', 'Roster read by', None, None), 'security_type': ('Security type', 'Roster source', 'Roster read by', None, None),
                 'isin': ('ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'ISIN'), 'sedol': ('SEDOL', 'SEDOL source', 'SEDOL read by', 'SEDOL State', 'SEDOL'), 'lei': ('LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI'),
                 'companies_house_number': ('Companies House number', 'Companies House source', 'Companies House read by', 'Companies House State', 'Companies House number'), 'companies_house_profile': ('Companies House profile link', 'Companies House source', 'Companies House read by', None, 'Companies House number'),
                 'registered_office': ('Registered office', 'Registered office source', 'Registered office read by', 'Registered office State', 'Registered office'), 'jurisdiction': ('Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State', 'Incorporation jurisdiction'),
                 'sic_codes': ('SIC code(s)', 'SIC source', 'SIC read by', 'SIC State', 'SIC code(s)'), 'sector': ('Sector (FTSE ICB)', 'Sector source', 'Sector read by', 'Sector State', 'Sector (FTSE ICB)'), 'sub_sector': ('Sub-sector', 'Sector source', 'Sector read by', None, None),
                 'auditor': ('Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Auditor'), 'accounts_filing': ('Accounts filing (Companies House)', None, 'Companies House read by', None, 'Companies House number'), 'accounts_period_end': ('Accounts period end', None, 'Accounts read by', None, None), 'going_concern': ('Going concern (accounts)', None, 'Accounts read by', None, None),
                 'registrar': ('Registrar', 'Registrar source', 'Registrar read by', 'Registrar State', 'Registrar'), 'newswire': ('Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State', 'Newswire of habit'),
                 'nsm_link': ('FCA NSM link (unverified — search entry)', None, 'NSM read by', None, 'FCA NSM link'), 'hq_city': ('HQ city', 'HQ source', 'HQ read by', 'HQ State', 'HQ city'), 'hq_country': ('HQ country', 'HQ source', 'HQ read by', None, 'HQ city'),
                 'website': ('Website', 'Website source', 'Website read by', None, None), 'admission_date': ('Admission date', 'Admission date source', 'Roster read by', None, 'Admission date')},
      'second': {'isin': 'ISIN', 'lei': 'LEI', 'companies_house_number': 'Companies House number', 'registrar': 'Registrar', 'auditor': 'Auditor', 'newswire': 'Newswire of habit', 'jurisdiction': 'Incorporation jurisdiction'}, 'prefixes': ['LSE', 'AIM', 'AQSE']}
AU = {'tabs': {'ASX': 'ASX', 'NSX': 'NSX', 'TMX Australia': 'TMX-AU'}, 'ticker': 'ASX code', 'name': 'Legal name', 'default_as_of': '2026-09-11',
      'fields': {'name': ('Legal name', 'Roster source', 'Roster read by', None, None), 'ticker': ('ASX code', 'Roster source', 'Roster read by', None, None), 'exchange': ('Exchange', 'Roster source', 'Roster read by', None, None),
                 'security_type': ('Security type', 'Roster source', 'Roster read by', None, None), 'share_description': ('Share description', 'Roster source', 'Roster read by', None, None),
                 'isin': ('ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'ISIN'), 'lei': ('LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI'), 'lei_registration_status': ('LEI registration status', 'LEI source', 'LEI read by', None, 'LEI'),
                 'acn': ('ACN', 'ASIC source', 'ASIC read by', 'ASIC State', 'ACN'), 'abn': ('ABN', 'ASIC source', 'ASIC read by', 'ASIC State', 'ACN'), 'asic_link': ('ASIC link (unverified — search entry)', None, 'ASIC read by', None, 'ACN'),
                 'asic_status': ('ASIC status', 'ASIC source', 'ASIC read by', None, 'ASIC status'), 'asic_registration_date': ('ASIC registration date', 'ASIC source', 'ASIC read by', None, 'ACN'),
                 'registered_office': ('Registered office', 'Registered office source', 'Registered office read by', 'Registered office State', 'Registered office'), 'state': ('State', 'State source', 'State read by', 'State State', 'State'),
                 'jurisdiction': ('Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State', 'Incorporation jurisdiction'),
                 'sector': ('GICS sector', 'Sector source', 'Sector read by', 'Sector State', 'GICS sector'), 'industry_group': ('GICS industry group', 'Sector source', 'Sector read by', None, 'GICS sector'),
                 'auditor': ('Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Auditor'), 'annual_report': ('Annual report (ASX announcement)', 'Annual report source', 'Annual report read by', None, 'Annual report (ASX announcement)'),
                 'accounts_period_end': ('Accounts period end', 'Auditor source', 'Auditor read by', None, None), 'going_concern': ('Going concern (annual report)', 'Auditor source', 'Auditor read by', None, None),
                 'share_registry': ('Share registry', 'Share registry source', 'Share registry read by', 'Share registry State', 'Share registry'), 'newswire': ('Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State', 'Newswire of habit'),
                 'asx_announcements_12m': ('ASX announcements (12 months)', 'ASX announcements link', 'Newswire read by', None, 'Newswire of habit'), 'asx_announcements_link': ('ASX announcements link', 'ASX announcements link', 'Newswire read by', None, 'Newswire of habit'),
                 'hq_city': ('HQ city', 'HQ source', 'HQ read by', 'HQ State', 'HQ city'), 'website': ('Website', 'Website source', 'Roster read by', None, None), 'listing_date': ('Listing date', 'Listing date source', 'Roster read by', None, 'Listing date')},
      'second': {'isin': 'ISIN', 'lei': 'LEI', 'acn': 'ACN', 'share_registry': 'Share registry', 'auditor': 'Auditor', 'newswire': 'Newswire of habit', 'state': 'State'}, 'prefixes': ['ASX', 'NSX']}
SG = {'tabs': {'SGX Mainboard': 'SGX', 'SGX Catalist': 'SGX-CATALIST'}, 'ticker': 'SGX code', 'name': 'Legal name', 'default_as_of': '2026-09-11',
      'fields': {'name': ('Legal name', 'Roster source', 'Roster read by', None, None), 'ticker': ('SGX code', 'Roster source', 'Roster read by', None, None), 'exchange': ('Market', 'Roster source', 'Roster read by', None, None),
                 'security_type': ('Security type', 'Roster source', 'Roster read by', None, None), 'trading_name': ('Trading name', 'Roster source', 'Roster read by', None, None), 'manager': ('Manager / depositary (SGX metadata issuer name)', 'ISIN source', 'ISIN read by', None, None),
                 'isin': ('ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'ISIN'), 'fisn': ('FISN', 'ISIN source', 'ISIN read by', None, None), 'lei': ('LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI'), 'lei_registration_status': ('LEI registration status', 'LEI source', 'LEI read by', None, 'LEI'),
                 'uen': ('UEN', 'ACRA source', 'ACRA read by', 'ACRA State', 'UEN'), 'acra_link': ('ACRA link (unverified — search entry)', None, 'ACRA read by', None, 'UEN'), 'acra_entity_type': ('ACRA entity type', 'ACRA source', 'ACRA read by', None, 'UEN'), 'acra_status': ('ACRA status', 'ACRA source', 'ACRA read by', None, 'UEN'), 'incorporation_date': ('Incorporation date', 'ACRA source', 'ACRA read by', None, 'UEN'),
                 'registered_office': ('Registered office', 'Registered office source', 'Registered office read by', 'Registered office State', 'Registered office'), 'jurisdiction': ('Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State', 'Incorporation jurisdiction'),
                 'sector': ('Sector (SGX)', 'Sector source', 'Sector read by', 'Sector State', 'Sector (SGX)'), 'ssic': ('Primary SSIC (ACRA)', 'ACRA source', 'ACRA read by', None, 'UEN'),
                 'auditor': ('Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Auditor'), 'annual_report': ('Annual report (SGXNet)', 'Annual report source', 'Annual report read by', None, 'Annual report (SGXNet)'),
                 'accounts_period_end': ('Accounts period end', 'Auditor source', 'Auditor read by', None, None), 'going_concern': ('Going concern (annual report)', 'Auditor source', 'Auditor read by', None, None),
                 'registrar': ('Share registrar', 'Share registrar source', 'Share registrar read by', 'Share registrar State', 'Share registrar'), 'newswire': ('Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State', 'Newswire of habit'),
                 'sgxnet_link': ('SGXNet announcements link', 'SGXNet announcements link', 'Newswire read by', None, None), 'hq_city': ('HQ city', 'HQ source', 'HQ read by', 'HQ State', 'HQ city'), 'listing_date': ('Listing date', 'Listing date source', 'Roster read by', None, 'Listing date'), 'trading_currency': ('Trading currency', 'Roster source', 'Roster read by', None, None)},
      'second': {'isin': 'ISIN', 'lei': 'LEI', 'uen': 'UEN', 'registrar': 'Share registrar', 'auditor': 'Auditor', 'newswire': 'Newswire of habit'}, 'prefixes': ['SGX', 'SGX-CATALIST']}
CH = {'tabs': {'SIX': 'SIX', 'BX Swiss': 'BX'}, 'ticker': 'Symbol', 'name': 'Legal name', 'default_as_of': '2026-09-11',
      'fields': {'name': ('Legal name', 'Roster source', 'Roster read by', None, None), 'ticker': ('Symbol', 'Roster source', 'Roster read by', None, None), 'exchange': ('Exchange', 'Roster source', 'Roster read by', None, None), 'valor': ('Valor', 'Roster source', 'Roster read by', None, None),
                 'security_type': ('Security type', 'Roster source', 'Roster read by', None, None), 'share_type': ('Share type', 'Roster source', 'Roster read by', None, None),
                 'isin': ('ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'ISIN'), 'lei': ('LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI'), 'lei_registration_status': ('LEI registration status', 'LEI source', 'LEI read by', None, 'LEI'),
                 'uid': ('UID (Zefix)', 'Zefix source', 'Zefix read by', 'Zefix State', 'UID (Zefix)'), 'ch_id': ('CH-ID', 'Zefix source', 'Zefix read by', None, 'UID (Zefix)'), 'zefix_excerpt': ('Zefix link (cantonal excerpt)', 'Zefix source', 'Zefix read by', None, 'UID (Zefix)'), 'legal_form': ('Legal form (Zefix)', 'Zefix source', 'Zefix read by', None, 'UID (Zefix)'), 'register_status': ('Zefix status', 'Zefix source', 'Zefix read by', None, 'UID (Zefix)'), 'last_shab_date': ('Last SHAB date', 'Zefix source', 'Zefix read by', None, 'UID (Zefix)'),
                 'legal_seat': ('Legal seat', 'Legal seat source', 'Legal seat read by', 'Legal seat State', 'Legal seat'), 'registered_office': ('Registered office', 'Registered office source', 'Registered office read by', 'Registered office State', 'Registered office'),
                 'jurisdiction': ('Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State', 'Incorporation jurisdiction'), 'sector': ('Sector (SIX ICB)', 'Sector source', 'Sector read by', 'Sector State', 'Sector (SIX ICB)'),
                 'auditor': ('Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Auditor'), 'annual_report': ('Annual report', 'Annual report source', 'Annual report read by', None, 'Annual report'), 'accounts_period_end': ('Accounts period end', 'Auditor source', 'Auditor read by', None, None), 'going_concern': ('Going concern (annual report)', 'Auditor source', 'Auditor read by', None, None),
                 'registrar': ('Share registrar', 'Share registrar source', 'Share registrar read by', 'Share registrar State', 'Share registrar'), 'newswire': ('Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State', 'Newswire of habit'),
                 'hq_city': ('HQ city', 'HQ source', 'HQ read by', 'HQ State', 'HQ city'), 'listing_date': ('Listing date', 'Listing date source', 'Roster read by', None, 'Listing date'), 'trading_currency': ('Trading currency', 'Roster source', 'Roster read by', None, None), 'number_in_issue': ('Number in issue', 'Roster source', 'Roster read by', None, None)},
      'second': {'isin': 'ISIN', 'lei': 'LEI', 'uid': 'UID (Zefix)', 'registrar': 'Share registrar', 'auditor': 'Auditor', 'newswire': 'Newswire of habit'}, 'prefixes': ['SIX', 'BX']}
DE = {'tabs': {'Xetra': 'XETRA'}, 'ticker': 'Symbol', 'name': 'Legal name', 'default_as_of': '2026-09-11',
      'fields': {'name': ('Legal name', 'Roster source', 'Roster read by', None, None), 'ticker': ('Symbol', 'Roster source', 'Roster read by', None, None), 'wkn': ('WKN', 'Roster source', 'Roster read by', None, None), 'exchange': ('Exchange', 'Roster source', 'Roster read by', None, None), 'segment': ('Segment (Xetra group)', 'Roster source', 'Roster read by', None, None),
                 'security_type': ('Security type', 'Roster source', 'Roster read by', None, None), 'isin': ('ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'ISIN'), 'lei': ('LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI'), 'lei_registration_status': ('LEI registration status', 'LEI source', 'LEI read by', None, 'LEI'),
                 'register_number': ('Register number (HR)', 'Register source', 'Register read by', 'Register State', 'Register number (HR)'), 'register_court': ('Register court', 'Register source', 'Register read by', None, 'Register number (HR)'), 'handelsregister_link': ('Handelsregister link (unverified — search entry)', None, 'Register read by', None, 'Register number (HR)'),
                 'registered_office': ('Registered office', 'Registered office source', 'Registered office read by', 'Registered office State', 'Registered office'), 'jurisdiction': ('Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State', 'Incorporation jurisdiction'),
                 'sector': ('Sector', 'Sector source', 'Sector read by', 'Sector State', 'Sector'), 'auditor': ('Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Auditor'), 'annual_report': ('Annual report (Bundesanzeiger)', 'Annual report source', 'Annual report read by', None, 'Annual report (Bundesanzeiger)'), 'accounts_period_end': ('Accounts period end', 'Auditor source', 'Auditor read by', None, None), 'going_concern': ('Going concern (annual report)', 'Auditor source', 'Auditor read by', None, None),
                 'registrar': ('Share registrar', 'Share registrar source', 'Share registrar read by', 'Share registrar State', 'Share registrar'), 'newswire': ('Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State', 'Newswire of habit'),
                 'hq_city': ('HQ city', 'HQ source', 'HQ read by', 'HQ State', 'HQ city'), 'designated_sponsor': ('Designated sponsor', 'Roster source', 'Roster read by', None, None), 'trading_currency': ('Trading currency', 'Roster source', 'Roster read by', None, None)},
      'second': {'isin': 'ISIN', 'lei': 'LEI', 'register_number': 'Register number (HR)', 'registrar': 'Share registrar', 'auditor': 'Auditor', 'newswire': 'Newswire of habit'}, 'prefixes': ['XETRA']}
FR = {'tabs': {'Euronext Paris': 'XPAR', 'Euronext Growth Paris': 'ALXP', 'Euronext Access Paris': 'XMLI'}, 'ticker': 'ISIN', 'name': 'Legal name', 'default_as_of': '2026-09-11',
      'fields': {'name': ('Legal name', 'Roster source', 'Roster read by', None, None), 'ticker': ('ISIN', 'Roster source', 'Roster read by', None, None), 'exchange': ('Exchange', 'Roster source', 'Roster read by', None, None),
                 'security_type': ('Security type', 'Roster source', 'Roster read by', None, None), 'cfi': ('CFI', 'Roster source', 'Roster read by', None, None), 'mic': ('MIC', 'Roster source', 'Roster read by', None, None), 'firds_short_name': ('FIRDS short name', 'Roster source', 'Roster read by', None, None),
                 'isin': ('ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'ISIN'), 'lei': ('LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI'), 'lei_registration_status': ('LEI registration status', 'LEI source', 'LEI read by', None, 'LEI'),
                 'registered_office': ('Registered office', 'Registered office source', 'Registered office read by', 'Registered office State', 'Registered office'), 'jurisdiction': ('Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State', 'Incorporation jurisdiction'),
                 'sector': ('Sector', 'Sector source', 'Sector read by', 'Sector State', 'Sector'), 'auditor': ('Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Auditor'), 'annual_report': ('Annual report', 'Annual report source', 'Annual report read by', None, 'Annual report'), 'accounts_period_end': ('Accounts period end', 'Auditor source', 'Auditor read by', None, None), 'going_concern': ('Going concern (annual report)', 'Auditor source', 'Auditor read by', None, None),
                 'registrar': ('Share registrar', 'Share registrar source', 'Share registrar read by', 'Share registrar State', 'Share registrar'), 'newswire': ('Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State', 'Newswire of habit'),
                 'hq_city': ('HQ city', 'HQ source', 'HQ read by', 'HQ State', 'HQ city'), 'listing_date': ('Listing date', 'Listing date source', 'Roster read by', None, 'Listing date'), 'trading_currency': ('Trading currency', 'Roster source', 'Roster read by', None, None), 'status': ('Status', 'Roster source', 'Roster read by', None, None),
                 'siren': ('SIREN', 'Register source', 'Register read by', 'Register State', 'SIREN'), 'register_link': ('Register link (Annuaire des entreprises)', 'Register source', 'Register read by', None, 'SIREN'), 'infogreffe_link': ('Infogreffe link (unverified — search entry)', None, 'Register read by', None, 'SIREN'), 'legal_form': ('Legal form (nature juridique)', 'Register source', 'Register read by', None, 'SIREN'), 'register_status': ('Register status', 'Register source', 'Register read by', None, 'SIREN'), 'date_of_creation': ('Date of creation', 'Register source', 'Register read by', None, 'SIREN'), 'naf_code': ('NAF code', 'Register source', 'Register read by', None, 'SIREN'),
                 'amf_filer_token': ('AMF filer token (BDIF)', 'AMF source', 'AMF read by', None, 'AMF filer token (BDIF)'), 'amf_bdif_link': ('AMF BDIF link', 'AMF source', 'AMF read by', None, 'AMF filer token (BDIF)')},
      'second': {'isin': 'ISIN', 'lei': 'LEI', 'siren': 'SIREN', 'registrar': 'Share registrar', 'auditor': 'Auditor', 'newswire': 'Newswire of habit'}, 'prefixes': ['XPAR', 'ALXP', 'XMLI'], 'alias_from_lei_record': True}
NL = {'tabs': {'Euronext Amsterdam': 'XAMS', 'Euronext Growth Amsterdam': 'ALXA'}, 'ticker': 'ISIN', 'name': 'Legal name', 'default_as_of': '2026-09-11',
      'fields': {'name': ('Legal name', 'Roster source', 'Roster read by', None, None), 'ticker': ('ISIN', 'Roster source', 'Roster read by', None, None), 'exchange': ('Exchange', 'Roster source', 'Roster read by', None, None),
                 'security_type': ('Security type', 'Roster source', 'Roster read by', None, None), 'cfi': ('CFI', 'Roster source', 'Roster read by', None, None), 'mic': ('MIC', 'Roster source', 'Roster read by', None, None), 'firds_short_name': ('FIRDS short name', 'Roster source', 'Roster read by', None, None),
                 'isin': ('ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'ISIN'), 'lei': ('LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI'), 'lei_registration_status': ('LEI registration status', 'LEI source', 'LEI read by', None, 'LEI'),
                 'registered_office': ('Registered office', 'Registered office source', 'Registered office read by', 'Registered office State', 'Registered office'), 'jurisdiction': ('Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State', 'Incorporation jurisdiction'),
                 'sector': ('Sector', 'Sector source', 'Sector read by', 'Sector State', 'Sector'), 'auditor': ('Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Auditor'), 'annual_report': ('Annual report', 'Annual report source', 'Annual report read by', None, 'Annual report'), 'accounts_period_end': ('Accounts period end', 'Auditor source', 'Auditor read by', None, None), 'going_concern': ('Going concern (annual report)', 'Auditor source', 'Auditor read by', None, None),
                 'registrar': ('Share registrar', 'Share registrar source', 'Share registrar read by', 'Share registrar State', 'Share registrar'), 'newswire': ('Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State', 'Newswire of habit'),
                 'hq_city': ('HQ city', 'HQ source', 'HQ read by', 'HQ State', 'HQ city'), 'listing_date': ('Listing date', 'Listing date source', 'Roster read by', None, 'Listing date'), 'trading_currency': ('Trading currency', 'Roster source', 'Roster read by', None, None), 'status': ('Status', 'Roster source', 'Roster read by', None, None),
                 'kvk_number': ('KVK number', 'Register source', 'Register read by', 'Register State', 'KVK number'), 'kvk_link': ('KVK link (unverified — search entry)', None, 'Register read by', None, 'KVK number'), 'legal_form': ('Legal form (GLEIF ELF code)', 'Register source', 'Register read by', None, 'KVK number'), 'afm_register_link': ('AFM issuer register link (unverified — search entry)', None, 'Register read by', None, None)},
      'second': {'isin': 'ISIN', 'lei': 'LEI', 'kvk_number': 'KVK number', 'registrar': 'Share registrar', 'auditor': 'Auditor', 'newswire': 'Newswire of habit'}, 'prefixes': ['XAMS', 'ALXA'], 'alias_from_lei_record': True}
MAPS = {'ca': CA, 'uk': UK, 'au': AU, 'sg': SG, 'ch': CH, 'de': DE, 'fr': FR, 'nl': NL}
def field(d, spec, gaps):
    vcol, scol, rcol, stcol, glabel = spec
    v = d.get(vcol)
    if v in (None, ''): return {'value': None, 'source_url': None, 'read_by': None, 'state': None, 'reason': gaps.get(glabel or vcol, 'no source read')}
    src = (d.get(scol) or '') if scol else ''
    if isinstance(src, str) and '\n' in src: src = src.split('\n')[0]
    st = (d.get(stcol) or 'sourced') if stcol else ('unverified' if 'unverified' in vcol else 'sourced')
    o = {'value': v if not isinstance(v, str) else v.strip(), 'source_url': src or None, 'read_by': d.get(rcol) or None, 'state': st}
    if isinstance(o['value'], str) and '[TMX workbook says' in o['value']:
        m = re.match(r'^(.*?)\s*\[TMX workbook says ([^\]]+)\]$', o['value'])
        if m and m.group(1).strip(): o['value'] = m.group(1).strip(); o['note'] = f'TMX workbook says {m.group(2)}'
        elif m: o['value'] = m.group(2).strip(); o['source_url'] = 'https://www.tsx.com/en/resource/571'; o['read_by'] = 'TMX listed-companies workbook (exchange list, monthly)'; o['state'] = 'sourced'
    if isinstance(o['value'], str) and '  [search by' in o['value']: o['value'], o['note'] = o['value'].split('  [', 1)[0], o['value'].split('  [', 1)[1].rstrip(']')
    return o
import pond  # pond rule 2: the loader reads the latest versioned outputs in POND\<node>\assembled\; the canonical ISSUERS / DISCLOSURE paths are the fallback for nodes assembled before the pond
def load_node(cc, index, facts_nodes):
    M = MAPS[cc]; node = f'{cc}-cm-kg'; host = f'https://mcp.{node}.ai'
    xlsx = pond.latest_assembled(node, f'{cc}-issuers.xlsx') or os.path.join(ROOT, rf'CM-KG\ISSUERS\{cc}-issuers.xlsx')
    evfn = pond.latest_assembled(node, f'{cc}-events.jsonl') or os.path.join(ROOT, rf'CM-KG\DISCLOSURE\events\{cc}-events.jsonl')
    print(node, 'inputs:', xlsx, '|', evfn)
    as_of = os.environ.get(f'AS_OF_{cc.upper()}', M['default_as_of']); version = int(os.environ.get(f'CMR_VERSION_{cc.upper()}', '1'))
    ev_by = {}
    if os.path.exists(evfn):
        for line in open(evfn, encoding='utf-8'):
            e = json.loads(line); ev_by.setdefault((e['exchange'], e['ticker']), []).append(e)
    lei_legal_names = {}
    if M.get('alias_from_lei_record'):
        for lr in pond.read_jsonl_all(node, 'width0', 'lei_records.jsonl'):
            lid = lr.get('lei') or lr.get('key')
            if lid and lr.get('name'): lei_legal_names[lid] = (lr['name'], lr.get('src') or f'https://api.gleif.org/api/v1/lei-records/{lid}')
    wb = openpyxl.load_workbook(xlsx, read_only=True); n = 0; counts = {}
    for tab, exs in M['tabs'].items():
        ws = wb[tab]; it = ws.iter_rows(values_only=True); hdr = next(it)
        os.makedirs(os.path.join(OUT, 'records', node, exs), exist_ok=True); os.makedirs(os.path.join(OUT, 'events', node, exs), exist_ok=True)
        for row in it:
            d = dict(zip(hdr, row))
            if not d.get(M['ticker']): continue
            t = str(d[M['ticker']]).strip(); key = f'{node}/{exs}/{t}'; gaps = gaps_of(d.get('Gaps'))
            identity = {f: field(d, spec, gaps) for f, spec in M['fields'].items() if spec[0] in d}
            for f, col in M['second'].items():
                if f in identity and identity[f]['value'] is not None:
                    s2 = d.get(f'{col} second source'); r2 = d.get(f'{col} second read by')
                    if s2: identity[f]['second_source_url'] = str(s2).split('\n')[0]
                    if r2: identity[f]['second_read_by'] = r2
            aliases = []
            if d.get('Also known as'):
                names = [a.strip() for a in str(d['Also known as']).split(' | ')]; srcs = str(d.get('Alias source') or '').split('\n'); rbs = str(d.get('Alias read by') or '').split('\n')
                for i, a in enumerate(names):
                    if a: aliases.append({'value': a, 'source_url': srcs[i] if i < len(srcs) else None, 'read_by': rbs[i] if i < len(rbs) else None})
            # Euronext nodes (FIRDS names carry no legal suffix): the GLEIF legal name rides as a sourced alias so 'TotalEnergies SE' resolves
            lei_v = (identity.get('lei') or {}).get('value')
            if M.get('alias_from_lei_record') and lei_v and lei_v in lei_legal_names and nkey(lei_legal_names[lei_v][0]) != nkey(d[M['name']]) and not any(nkey(a['value']) == nkey(lei_legal_names[lei_v][0]) for a in aliases):
                aliases.append({'value': lei_legal_names[lei_v][0], 'source_url': lei_legal_names[lei_v][1], 'read_by': 'GLEIF LEI record (legal name)'})
            evs = sorted(ev_by.get((tab, t), []), key=lambda e: e['date'], reverse=True)
            rec = {'cmr': key, 'node': node, 'as_of': as_of, 'version': version, 'identity': identity, 'aliases': aliases, 'events_url': f'{host}/events/{exs}/{t}', 'event_count': len(evs), 'gaps': [{'field': f, 'reason': w} for f, w in gaps.items()]}
            json.dump(rec, open(os.path.join(OUT, 'records', node, exs, slug_ticker(t) + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            json.dump([{k2: e.get(k2) for k2 in ('date', 'event_type', 'title', 'rns_category', 'ch_filing_type', 'asx_category', 'price_sensitive', 'sgx_category', 'reference', 'category', 'language', 'wire', 'source', 'url', 'read_by', 'state', 'detail', 'second_source', 'second_read_by', 'period_end', 'statement_date', 'auditor_named', 'going_concern', 'extract_read_by') if e.get(k2) not in (None, '')} for e in evs],
                      open(os.path.join(OUT, 'events', node, exs, slug_ticker(t) + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            index['keys'].append(key); index['ticker'].setdefault(t.upper(), []).append(key)
            root = t.split('.')[0].upper()
            if root != t.upper(): index['ticker'].setdefault(root, []).append(key)
            for a in aliases: index['alias'].setdefault(nkey(a['value']), []).append(key)
            index['name'].setdefault(nkey(d[M['name']]), []).append(key)
            if identity.get('isin', {}).get('value'): index['isin'].setdefault(identity['isin']['value'].upper(), []).append(key)
            if identity.get('lei', {}).get('value'): index['lei'].setdefault(identity['lei']['value'].upper(), []).append(key)
            counts[exs] = counts.get(exs, 0) + 1; n += 1
    # Reference records beside the issuer records (Eurex on de-cm-kg, CEO go 2026-09-11): <cc>-ref-records.jsonl / <cc>-ref-events.jsonl in the latest
    # assembled drop. Same record shape, own exchange code; their ISINs are not indexed (an ISIN lookup resolves to the issuer, never to a derivative);
    # when a record names its underlying's CMR key, the issuer record gets the product list written on it with the same provenance.
    rp = pond.latest_assembled(node, f'{cc}-ref-records.jsonl'); ep = pond.latest_assembled(node, f'{cc}-ref-events.jsonl'); ref_ev = {}; by_under = {}; extra_ex = []
    if rp:
        print(node, 'reference inputs:', rp, '|', ep)
        if ep:
            for line in open(ep, encoding='utf-8'):
                e = json.loads(line); ref_ev.setdefault((e['exchange'], e['ticker']), []).append(e)
        for line in open(rp, encoding='utf-8'):
            r = json.loads(line); exs = r['exchange']; t = str(r['ticker']); key = r['cmr']
            if exs not in extra_ex: extra_ex.append(exs); os.makedirs(os.path.join(OUT, 'records', node, exs), exist_ok=True); os.makedirs(os.path.join(OUT, 'events', node, exs), exist_ok=True)
            evs = sorted(ref_ev.get((exs, t), []), key=lambda e: e['date'], reverse=True)
            rec = {'cmr': key, 'node': node, 'as_of': r.get('as_of') or as_of, 'version': r.get('version', 1), 'kind': r.get('kind'), 'identity': r['identity'], 'aliases': r.get('aliases', []), 'events_url': f'{host}/events/{exs}/{t}', 'event_count': len(evs), 'gaps': r.get('gaps', []), 'sources': r.get('sources')}
            json.dump(rec, open(os.path.join(OUT, 'records', node, exs, slug_ticker(t) + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            json.dump([{k2: e.get(k2) for k2 in ('date', 'event_type', 'title', 'reference', 'category', 'language', 'wire', 'source', 'url', 'read_by', 'state', 'detail') if e.get(k2) not in (None, '')} for e in evs], open(os.path.join(OUT, 'events', node, exs, slug_ticker(t) + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            index['keys'].append(key); index['ticker'].setdefault(t.upper(), []).append(key)
            for a in rec['aliases']: index['alias'].setdefault(nkey(a['value']), []).append(key)
            nm = (r['identity'].get('name') or {}).get('value') or r.get('name')
            if nm: index['name'].setdefault(nkey(nm), []).append(key)
            u = (r['identity'].get('underlying_cmr') or {}).get('value')
            if u: by_under.setdefault(u, []).append({'cmr': key, 'product': t, 'name': nm, 'product_line': (r['identity'].get('product_line') or {}).get('value'), 'source_url': (r['identity'].get('underlying_cmr') or {}).get('source_url'), 'read_by': (r['identity'].get('underlying_cmr') or {}).get('read_by')})
            counts[exs] = counts.get(exs, 0) + 1; n += 1
            if evs: ev_by[(exs, t)] = evs
        for ucmr, prods in by_under.items():
            parts = ucmr.split('/'); fp = os.path.join(OUT, 'records', parts[0], parts[1], slug_ticker(parts[2]) + '.json')
            if not os.path.exists(fp): continue
            irec = json.load(open(fp, encoding='utf-8'))
            irec['identity']['eurex_products'] = {'value': ', '.join(p['product'] for p in prods), 'records': [p['cmr'] for p in prods], 'source_url': prods[0]['source_url'], 'read_by': prods[0]['read_by'], 'state': 'sourced', 'note': 'Eurex products whose underlying ISIN is this issuer (reference-data door)'}
            json.dump(irec, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        print(node, 'reference records', sum(counts.get(x, 0) for x in extra_ex), extra_ex, '| issuer records linked', len(by_under))
    facts_nodes[node] = {'as_of': as_of, 'version': version, 'records': n, 'records_by_exchange': counts, 'events': sum(len(v) for v in ev_by.values()), 'issuers_with_events': len(ev_by), 'exchanges': list(M['tabs'].values()) + extra_ex}
    print(node, 'records', n, counts, '| events', facts_nodes[node]['events'], 'issuers with events', len(ev_by))
def main():
    want = [a for a in sys.argv[1:] if a in MAPS] or [cc for cc in MAPS if os.path.exists(os.path.join(ROOT, rf'CM-KG\ISSUERS\{cc}-issuers.xlsx'))]
    index = {'ticker': {}, 'isin': {}, 'lei': {}, 'alias': {}, 'name': {}, 'keys': []}; facts_nodes = {}
    for sub in ('records', 'events'): os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    for cc in want: load_node(cc, index, facts_nodes)
    json.dump(index, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), separators=(',', ':'))
    facts = {'as_of': max(v['as_of'] for v in facts_nodes.values()), 'records': sum(v['records'] for v in facts_nodes.values()), 'events': sum(v['events'] for v in facts_nodes.values()), 'nodes': facts_nodes,
             'source': 'public-record', 'operator': 'Allooloo Technologies Corp.', 'store': 'Cloudflare Workers Static Assets (one JSON per record and per issuer events)',
             'tools': ['resolve_issuer', 'get_record', 'list_events_since', 'list_aliases', 'list_nodes'], 'mcp': '/mcp (Streamable HTTP, JSON-RPC 2.0, no auth)'}
    json.dump(facts, open(os.path.join(OUT, 'facts.json'), 'w', encoding='utf-8'), indent=1)
    nodes = [{'node': f'{c}-cm-kg', 'country': nme, 'registry': f'{c}-cm-kg.org', 'door': f'https://mcp.{c}-cm-kg.ai', 'live': f'{c}-cm-kg' in facts_nodes, 'as_of': facts_nodes.get(f'{c}-cm-kg', {}).get('as_of'), 'records': facts_nodes.get(f'{c}-cm-kg', {}).get('records', 0), 'exchanges': facts_nodes.get(f'{c}-cm-kg', {}).get('exchanges', [])} for c, nme in NODES]
    json.dump(nodes, open(os.path.join(OUT, 'nodes.json'), 'w', encoding='utf-8'), indent=1)
    static_dir = os.path.join(ROOT, r'CM-KG\DOOR\static')
    if os.path.isdir(static_dir):
        for f in os.listdir(static_dir): shutil.copy(os.path.join(static_dir, f), os.path.join(OUT, f))
    # retire the pre-ORDER-010 flat layout (records/<EX>/…) once the node layout exists: the same records live under records/ca-cm-kg/
    for sub in ('records', 'events'):
        for ex in ('TSX', 'TSXV', 'CSE', 'CBOE-CANADA'):
            p = os.path.join(OUT, sub, ex)
            if os.path.isdir(p) and os.path.isdir(os.path.join(OUT, sub, 'ca-cm-kg', ex)): shutil.rmtree(p)
    nfiles = sum(len(fs) for _, _, fs in os.walk(OUT))
    print('index tickers', len(index['ticker']), 'isins', len(index['isin']), 'leis', len(index['lei']), '| files in data/', nfiles, '(Workers static-assets cap 20,000 per version)')
    if nfiles > 20000: print('FILE CAP EXCEEDED — STOP per ORDER-010 Part A step 4')
if __name__ == '__main__': main()
