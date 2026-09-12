# ORDER-017 — Beacons on the weekly sweep: Japan, South Korea, Hong Kong, United States
Date: Sept 11 2026 · Width 0 ONLY, no Fill, no labs, no doors · pond-native · runs weekly from first drop.

- Japan: JPX listed-issuer list (public monthly file); EDINET has a FREE API (filer identity, EDINET code) — register a key
  if required (HITL); GLEIF. Records land on the global door as not-live.
- South Korea: KRX listed list (KIND, public); DART has a FREE API key (HITL: register); GLEIF.
- Hong Kong: HKEX list of securities (public file); Companies Registry link only. Width 0 only — partner node by CEO ruling;
  node page carries the local-partner copy of record.
- United States: SEC company tickers JSON + EDGAR submissions API (free, no key, fair-use rate) — identity, CIK, SIC, state;
  GLEIF (US ISINs mapped). Width 0 only; US is last by CEO ruling.
Output <cc>-issuers.xlsx per node; weekly drop; report counts, sources answered/refused, HITL, spend (should be Tavily only).
