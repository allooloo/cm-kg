// ORDER-027 D2 — one real wire capture per duty door, taken from the node door on 2026-10-17 (resolve_issuer, then list_events_since). Verbatim; never edited.
export default {
 "kyp": {
  "node": "ca-cm-kg",
  "identifier": "TSX:DSV",
  "resolve": {
   "cmr": "ca-cm-kg/TSX/DSV",
   "node": "ca-cm-kg",
   "version": 1,
   "as_of": "2026-10-17",
   "name": "Discovery Mining Ltd.",
   "ticker": "DSV",
   "exchange": "TSX",
   "security_type": "Corporate",
   "isin": null,
   "lei": null,
   "sector": "Mining",
   "event_count": 21,
   "events_url": "https://mcp.ca-cm-kg.ai/events/TSX/DSV",
   "record_url": "https://mcp.ca-cm-kg.ai/record/TSX/DSV"
  },
  "events": {
   "cmr": "ca-cm-kg/TSX/DSV",
   "since": "2026-10-01",
   "total": 3,
   "cursor": 0,
   "limit": 3,
   "next_cursor": null,
   "events": [
    {
     "date": "2026-10-09",
     "event_type": "newswire_release",
     "title": "Discovery Enters into Asset Purchase Agreement to Acquire",
     "wire": "GlobeNewswire",
     "source": "GlobeNewswire",
     "url": "https://www.globenewswire.com/news-release/2026/10/09/3378103/0/en/discovery-enters-into-asset-purchase-agreement-to-acquire-certain-timmins-mineral-properties-from-mcewen-inc.html",
     "read_by": "Tavily search (wire domains) + published_date",
     "state": "filled"
    },
    {
     "date": "2026-10-07",
     "event_type": "newswire_release",
     "title": "Discovery Reports New, High-Grade Intersections at Pamour",
     "wire": "GlobeNewswire",
     "source": "GlobeNewswire",
     "url": "https://www.globenewswire.com/news-release/2026/10/07/3376904/0/en/discovery-reports-new-high-grade-intersections-at-pamour-that-further-extend-mineralization-along-strike-to-the-north-and-to-depth.html",
     "read_by": "Tavily search (wire domains) + published_date",
     "state": "filled"
    },
    {
     "date": "2026-10-05",
     "event_type": "newswire_release",
     "title": "Discovery Announces Receipt of Key Environmental and Land",
     "wire": "GlobeNewswire",
     "source": "GlobeNewswire",
     "url": "https://www.globenewswire.com/news-release/2026/10/05/3374916/0/en/discovery-announces-receipt-of-key-environmental-and-land-use-permits-for-cordero-project.html",
     "read_by": "Tavily search (wire domains) + published_date",
     "state": "filled"
    }
   ]
  },
  "captured": "2026-10-17"
 },
 "prod": {
  "node": "uk-cm-kg",
  "identifier": "LSE:AZN",
  "resolve": {
   "cmr": "uk-cm-kg/LSE/AZN",
   "node": "uk-cm-kg",
   "version": 1,
   "as_of": "2026-10-17",
   "name": "ASTRAZENECA PLC",
   "ticker": "AZN",
   "exchange": "LSE Main Market",
   "security_type": "Corporate",
   "isin": "GB0009895292",
   "lei": "PY6ZZQWO2IZFZC3IOL08",
   "sector": "Pharmaceuticals and Biotechnology [201030]",
   "event_count": 140,
   "events_url": "https://mcp.uk-cm-kg.ai/events/LSE/AZN",
   "record_url": "https://mcp.uk-cm-kg.ai/record/LSE/AZN"
  },
  "events": {
   "cmr": "uk-cm-kg/LSE/AZN",
   "since": "2026-10-01",
   "total": 3,
   "cursor": 0,
   "limit": 3,
   "next_cursor": null,
   "events": [
    {
     "date": "2026-10-05",
     "event_type": "ch_capital",
     "title": "capital allotment shares — 2026-09-23",
     "ch_filing_type": "capital",
     "source": "Companies House",
     "url": "https://find-and-update.company-information.service.gov.uk/company/02723534/filing-history/MzU0ODIzNzExN2FkaXF6a2N4/document?format=pdf&download=0",
     "read_by": "Companies House REST API (filing history)",
     "detail": "form SH01; category capital"
    },
    {
     "date": "2026-10-05",
     "event_type": "regulatory_announcement",
     "title": "AstraZeneca completes equity investment in Summit",
     "rns_category": "AstraZeneca completes equity investment in Summit",
     "wire": "RNS",
     "source": "Regulatory announcement via Investegate (RNS)",
     "url": "https://www.investegate.co.uk/announcement/rns/astrazeneca--azn/astrazeneca-completes-equity-investment-in-summit/9806986",
     "read_by": "investegate.co.uk company page (RNS mirror)",
     "detail": "RIS source RNS"
    },
    {
     "date": "2026-10-02",
     "event_type": "regulatory_announcement",
     "title": "AZ & DS collaboration with Summit for Datroway",
     "rns_category": "AZ & DS collaboration with Summit for Datroway",
     "wire": "RNS",
     "source": "Regulatory announcement via Investegate (RNS)",
     "url": "https://www.investegate.co.uk/announcement/rns/astrazeneca--azn/az-ds-collaboration-with-summit-for-datroway/9803807",
     "read_by": "investegate.co.uk company page (RNS mirror)",
     "detail": "RIS source RNS"
    }
   ]
  },
  "captured": "2026-10-17"
 },
 "mifid": {
  "node": "de-cm-kg",
  "identifier": "ALV.DE",
  "resolve": {
   "cmr": "de-cm-kg/XETRA/ALV",
   "node": "de-cm-kg",
   "version": 1,
   "as_of": "2026-10-16",
   "name": "ALLIANZ SE NA O.N.",
   "ticker": "ALV",
   "exchange": "Xetra",
   "security_type": "Corporate",
   "isin": "DE0008404005",
   "lei": "529900K9B0N5BT694847",
   "sector": null,
   "event_count": 15,
   "events_url": "https://mcp.de-cm-kg.ai/events/XETRA/ALV",
   "record_url": "https://mcp.de-cm-kg.ai/record/XETRA/ALV"
  },
  "events": {
   "cmr": "de-cm-kg/XETRA/ALV",
   "since": "2026-10-01",
   "total": 2,
   "cursor": 0,
   "limit": 3,
   "next_cursor": null,
   "events": [
    {
     "date": "2026-10-08",
     "event_type": "newswire_release",
     "title": "Allianz: Companies Experience Sharp Increase in ...",
     "wire": "Business Wire",
     "source": "Business Wire",
     "url": "https://www.businesswire.com/news/home/20261008744523/en/Allianz-Companies-Experience-Sharp-Increase-in-Business-Interruption-Losses",
     "read_by": "Tavily search (wire domains) + published_date"
    },
    {
     "date": "2026-10-07",
     "event_type": "newswire_release",
     "title": "Ledgebrook raises USD 200 million in primary equity financing co-led by Allianz X to scale AI-native specialty insurance platform",
     "wire": "PR Newswire",
     "source": "PR Newswire",
     "url": "https://www.prnewswire.com/news-releases/ledgebrook-raises-usd-200-million-in-primary-equity-financing-co-led-by-allianz-x-to-scale-ai-native-specialty-insurance-platform-302899921.html",
     "read_by": "Tavily search (wire domains) + published_date"
    }
   ]
  },
  "captured": "2026-10-17"
 },
 "finsa": {
  "node": "ch-cm-kg",
  "identifier": "NOVN.SW",
  "resolve": {
   "cmr": "ch-cm-kg/SIX/NOVN",
   "node": "ch-cm-kg",
   "version": 1,
   "as_of": "2026-10-16",
   "name": "NOVARTIS N",
   "ticker": "NOVN",
   "exchange": "SIX",
   "security_type": "Corporate",
   "isin": "CH0012005267",
   "lei": "5493007HIVTX6SY6XD66",
   "sector": null,
   "event_count": 29,
   "events_url": "https://mcp.ch-cm-kg.ai/events/SIX/NOVN",
   "record_url": "https://mcp.ch-cm-kg.ai/record/SIX/NOVN"
  },
  "events": {
   "cmr": "ch-cm-kg/SIX/NOVN",
   "since": "2026-10-01",
   "total": 10,
   "cursor": 0,
   "limit": 3,
   "next_cursor": 3,
   "events": [
    {
     "date": "2026-10-09",
     "event_type": "register_mutation",
     "title": "HR02 Change Novartis Stiftung für Kaderausbildung, Basel",
     "reference": "HR02-1006779101",
     "category": "HR02",
     "language": "de",
     "source": "SHAB / FOSC commercial register publication",
     "url": "https://www.shab.ch/#!/search/publications/detail/6ef65402-490b-4dc5-acd6-d21f953c2015",
     "read_by": "SHAB publications API (Swiss Official Gazette of Commerce, commercial-register rubric)",
     "detail": "publication HR02-1006779101; office Bundesamt für Justiz (BJ), Eidgenössisches Amt für das Handelsregister"
    },
    {
     "date": "2026-10-09",
     "event_type": "register_mutation",
     "title": "HR02 Change Novartis Sanierungsstiftung, Basel",
     "reference": "HR02-1006779100",
     "category": "HR02",
     "language": "de",
     "source": "SHAB / FOSC commercial register publication",
     "url": "https://www.shab.ch/#!/search/publications/detail/ee64fb4a-12f2-47b3-bcc1-192fc2929ecb",
     "read_by": "SHAB publications API (Swiss Official Gazette of Commerce, commercial-register rubric)",
     "detail": "publication HR02-1006779100; office Bundesamt für Justiz (BJ), Eidgenössisches Amt für das Handelsregister"
    },
    {
     "date": "2026-10-08",
     "event_type": "newswire_release",
     "title": "INVESTOR ALERT: Pomerantz Law Firm Investigates Claims On Behalf of Investors of Novartis AG - NVS",
     "wire": "PR Newswire",
     "source": "PR Newswire",
     "url": "https://www.prnewswire.com/news-releases/investor-alert-pomerantz-law-firm-investigates-claims-on-behalf-of-investors-of-novartis-ag---nvs-302902146.html",
     "read_by": "Tavily search (wire domains) + published_date"
    }
   ]
  },
  "captured": "2026-10-17"
 },
 "ddo": {
  "node": "au-cm-kg",
  "identifier": "ASX:CBA",
  "resolve": {
   "cmr": "au-cm-kg/ASX/CBA",
   "node": "au-cm-kg",
   "version": 1,
   "as_of": "2026-10-17",
   "name": "COMMONWEALTH BANK OF AUSTRALIA.",
   "ticker": "CBA",
   "exchange": "ASX",
   "security_type": "Corporate",
   "isin": "AU000000CBA7",
   "lei": "MSFSBD3QN1GSN7Q6C537",
   "sector": "Financials",
   "event_count": 165,
   "events_url": "https://mcp.au-cm-kg.ai/events/ASX/CBA",
   "record_url": "https://mcp.au-cm-kg.ai/record/ASX/CBA"
  },
  "events": {
   "cmr": "au-cm-kg/ASX/CBA",
   "since": "2026-10-01",
   "total": 9,
   "cursor": 0,
   "limit": 3,
   "next_cursor": 3,
   "events": [
    {
     "date": "2026-10-14",
     "event_type": "agm_record_date",
     "title": "2026 Annual General Meeting Results",
     "asx_category": "2026 Annual General Meeting Results",
     "price_sensitive": "false",
     "wire": "ASX",
     "source": "ASX announcements platform",
     "url": "https://www.asx.com.au/asx/v2/statistics/displayAnnouncement.do?display=pdf&idsId=03152439",
     "read_by": "asx.com.au announcements search (exchange site)"
    },
    {
     "date": "2026-10-14",
     "event_type": "agm_record_date",
     "title": "2026 Annual General Meeting - CEO's Address",
     "asx_category": "2026 Annual General Meeting - CEO's Address",
     "price_sensitive": "false",
     "wire": "ASX",
     "source": "ASX announcements platform",
     "url": "https://www.asx.com.au/asx/v2/statistics/displayAnnouncement.do?display=pdf&idsId=03152037",
     "read_by": "asx.com.au announcements search (exchange site)"
    },
    {
     "date": "2026-10-14",
     "event_type": "agm_record_date",
     "title": "2026 Annual General Meeting - Chair's Address",
     "asx_category": "2026 Annual General Meeting - Chair's Address",
     "price_sensitive": "false",
     "wire": "ASX",
     "source": "ASX announcements platform",
     "url": "https://www.asx.com.au/asx/v2/statistics/displayAnnouncement.do?display=pdf&idsId=03152027",
     "read_by": "asx.com.au announcements search (exchange site)"
    }
   ]
  },
  "captured": "2026-10-17"
 },
 "regbi": {
  "node": "us-cm-kg",
  "identifier": "NYSE:JPM",
  "resolve": {
   "cmr": "us-cm-kg/NYSE/JPM",
   "node": "us-cm-kg",
   "version": 1,
   "as_of": "2026-10-17",
   "name": "JPMORGAN CHASE & CO",
   "ticker": "JPM",
   "exchange": "NYSE",
   "security_type": "Corporate",
   "isin": null,
   "lei": "8I5DZWZKVSZI1NUHU748",
   "sector": "6021 National Commercial Banks",
   "event_count": 26349,
   "events_url": "https://mcp.us-cm-kg.ai/events/NYSE/JPM",
   "record_url": "https://mcp.us-cm-kg.ai/record/NYSE/JPM"
  },
  "events": {
   "cmr": "us-cm-kg/NYSE/JPM",
   "since": "2026-10-01",
   "total": 1203,
   "cursor": 0,
   "limit": 3,
   "next_cursor": 3,
   "events": [
    {
     "date": "2026-10-16",
     "event_type": "prospectus",
     "title": "424B2 — PRICING SUPPLEMENT",
     "category": "424B2",
     "reference": "0001213900-26-110359",
     "language": "en",
     "wire": "EDGAR",
     "source": "SEC EDGAR filing index",
     "url": "https://www.sec.gov/Archives/edgar/data/19617/000121390026110359/ea0308868-01_424b2.htm",
     "read_by": "EDGAR submissions API (filings list per CIK)",
     "detail": "report date ",
     "state": "sourced"
    },
    {
     "date": "2026-10-16",
     "event_type": "prospectus",
     "title": "424B2 — PRICING SUPPLEMENT",
     "category": "424B2",
     "reference": "0001213900-26-110357",
     "language": "en",
     "wire": "EDGAR",
     "source": "SEC EDGAR filing index",
     "url": "https://www.sec.gov/Archives/edgar/data/19617/000121390026110357/ea0308932-01_424b2.htm",
     "read_by": "EDGAR submissions API (filings list per CIK)",
     "detail": "report date ",
     "state": "sourced"
    },
    {
     "date": "2026-10-16",
     "event_type": "prospectus",
     "title": "424B2 — PRICING SUPPLEMENT",
     "category": "424B2",
     "reference": "0001213900-26-110355",
     "language": "en",
     "wire": "EDGAR",
     "source": "SEC EDGAR filing index",
     "url": "https://www.sec.gov/Archives/edgar/data/19617/000121390026110355/ea0308933-01_424b2.htm",
     "read_by": "EDGAR submissions API (filings list per CIK)",
     "detail": "report date ",
     "state": "sourced"
    }
   ]
  },
  "captured": "2026-10-17"
 }
};
