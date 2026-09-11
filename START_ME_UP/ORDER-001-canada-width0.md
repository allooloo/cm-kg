# ORDER-001 — Canada Width 0 sweep
Date: Sept 10 2026 · Node: ca-cm-kg · Fly by wire.

## Do
1. Pull every listed issuer on TSX, TSXV, CSE, and Cboe Canada from the exchanges' public
   issuer lists. Harvest with Tavily + Perplexity Search; no scraping behind a login.
2. Enrich each row: legal name · ticker · exchange · listing tier · ISIN · LEI (GLEIF) ·
   sector · incorporation jurisdiction · SEDAR+ profile link · SEDI link · transfer agent ·
   auditor · newswire of habit (from the last three releases) · headquarters city/province.
3. Write CM-KG\ISSUERS\ca-issuers.xlsx: one tab per exchange, a Coverage tab with live
   COUNTA formulas, AutoFilter, frozen header, Arial. Every enriched field carries a
   source URL column and a "read by" column naming the lab or search layer that filled it.
4. Blank is blank. Never infer a transfer agent, auditor, or newswire — leave the cell empty
   and flag it in a Gaps tab with the row count.
5. Report: issuer count per exchange, fill rate per field, the Gaps count, and what is broken.

## Don't
- No test harness before the run. Run it.
- No prices, quotes, or market data of any kind.
- No reference to any other company's estate, code, or canon.
