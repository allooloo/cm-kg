# de-eurex — Deutsche Börse door on the Germany node (CEO go, Sept 11 2026)

Eurex derivatives reference data attached to `de-cm-kg` as a sourced reference-data door, the same five MCP tools and headers as every node door. Source: Deutsche Börse developer portal, app `allooloo-cm-kg`, API "Eurex-Data via GraphQL", endpoint `https://api.developer.deutsche-boerse.com/eurex-prod-graphql/`, header `X-DBP-APIKEY` from `AGENT KEYS\deutsche-boerse.txt` (read in-process, never printed). No paid Deutsche Börse product (A7, Cloud Stream, Data Shop) is subscribed. This API does not carry the Xetra Regulated Market / Scale segment flag: that column on `de-issuers` stays blank with its reason.

Pond-native: `raw\` is a junction to the open drop `CM-KG\POND\de-cm-kg\eurex\<date>\`; `assemble_eurex.py` reads every drop (newest wins per product) and writes a new versioned drop under `POND\de-cm-kg\assembled\<date>\` beside the issuer outputs, never on top of them.

## Steps
1. `fetch_eurex.py [Query …]` — pages of 1,000 rows by cursor (the API answers Internal Server Error above 1,000): `ProductInfos`, `TradingHours`, `TESProfiles`, `Expirations`, `Contracts`. Not read: `SettlementPrices` (prices are never carried on CM-KG), `TickRules`, `VendorCodes`, `Holidays`, `DeliverableBonds`, `Changelog`, `Enlight`, `EnlightResponders`, `FlexibleContracts` (outside the order). Price-shaped fields on the in-scope types are dropped at fetch (`PreviousDaySettlementPrice`, `OptionsDelta`, `MaxPrice`). Resumable per query (`<Query>.meta.json` keeps the cursor).
2. `assemble_eurex.py` — `de-ref-records.jsonl` (one door record per product, key `de-cm-kg/EUREX/<Product>`; every identity field carries the query URL as source, the read-by label and State sourced; trading hours and TES profiles ride on the record; contracts are counted and summarised, the rows stay in the drop; `underlying_cmr` links the Xetra issuer when the underlying ISIN is on the roster), `de-ref-events.jsonl` (one `contract_expiration` event per expiration, dated on the expiration date), `de-eurex.xlsx` (Products, Trading hours, TES profiles, Expirations, Contracts summary, Method; mirrored as a new file `CM-KG\REFERENCE\de-eurex.xlsx`).
3. `RAILS\door\load_nodes.py` — reads `<cc>-ref-records.jsonl` / `<cc>-ref-events.jsonl` from the latest assembled drop beside the issuer workbook, renders the EUREX records and events, and writes `eurex_products` onto each linked Xetra issuer record with the same provenance. `load_d1.py de-cm-kg` loads D1; `wrangler deploy` from `CM-KG\DOOR`.
4. Worker: exchange code `EUREX` on the Germany node (`EUREX:FDAX`, `XEUR:ODAX`, `de-cm-kg/EUREX/SAP`); a bare code (`SAP`) resolves to the issuer, never to the derivative product; product names and underlying names are sourced aliases.

## First run — 2026-09-11 (data dates 2026-09-12 products and contracts, 2026-09-14 hours, TES profiles and expirations; assembled drop 2026-09-11-12)
| Table | Rows | On the door |
|---|---|---|
| ProductInfos | 3,016 products (2,011 futures, 1,005 options; underlying categories: single stocks 2,142, indices 441, stock dividends 350, futures 39, currencies 27, debt 12, interest rate 4, commodities 1) | 3,016 records |
| Expirations | 33,700 | 33,700 `contract_expiration` events |
| TradingHours | 3,084 | on the record |
| TESProfiles | 20,753 | on the record |
| Contracts | 688,114 (3,018 products) | counted and summarised on the record; rows in the drop |

Germany node after the load: records 420 → 3,436 (XETRA 420 + EUREX 3,016), events 1,703 → 35,403. 435 products link to 153 Xetra issuer records, which now carry `eurex_products`.

Refresh: rerun steps 1–3 into a new drop (no scheduled task; global BUILD lock).
