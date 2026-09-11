# ORDER-007 — United Kingdom Width 0 sweep
Date: Sept 11 2026 · Node: uk-cm-kg · Fly by wire. Same rails as Canada (CM-KG\RAILS\ca-width0), pointed at UK sources.

## Scope
Every listed issuer on the London Stock Exchange Main Market and AIM, plus Aquis Stock Exchange (Access and Apex).
Output: CM-KG\ISSUERS\uk-issuers.xlsx (one tab per market, Coverage, Gaps, Method) and one CMR per row on the node.

## Do
1. Roster from the exchanges' public issuer lists (LSE publishes a full list of companies; Aquis its own). No login.
2. Enrich each row: legal name · ticker (TIDM) · market and segment · ISIN · SEDOL if published · LEI (GLEIF mapping
   file — GB-prefixed ISINs are expected to be present, unlike Canada; name-exact fallback per the Canada rule) ·
   Companies House number · registered office · incorporation jurisdiction (England & Wales / Scotland / NI / overseas) ·
   SIC code · sector (FTSE ICB if on the exchange list) · auditor (Companies House accounts filing — a source, not a read) ·
   registrar (Computershare / Equiniti / MUFG-Link / Neville — from the issuer's own page or the annual report) ·
   newswire of habit (RNS via LSE, or PR Newswire / GlobeNewswire / Business Wire from the last three releases) ·
   FCA National Storage Mechanism link · Companies House profile link · headquarters city.
3. Companies House: use the public web pages and the free API where a key exists in AGENT KEYS\companieshouse.txt;
   if no key file exists, web pages only and note it. This registry answers machines — record that on the Method tab;
   it is the first source in the estate that does.
4. Every enriched field carries source URL, read-by and State. Blank is blank. Never infer registrar, auditor or newswire.
5. Rails under CM-KG\RAILS\uk-width0\ with README (workers, sources, read-by labels, known-broken list).
6. Report: issuer count per market, fill rate per field, Gaps count, which UK sources answered machines and which refused,
   and what is broken.

## Don't
- No test harness before the run. No prices or market data. No fetch behind a login.
- No reference to any other company's estate, code, or canon.
