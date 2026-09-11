# CM-KG door — `cm-kg-door` (Cloudflare Worker)

One codebase, four hosts (ORDER-005 September 10 2026; ORDER-010 September 11 2026 added the United Kingdom node; ORDER-013 the same day added Australia):

| Host | Scope |
|---|---|
| `mcp.ca-cm-kg.ai` | Canada node door: TSX, TSXV, CSE, Cboe Canada. |
| `mcp.uk-cm-kg.ai` | United Kingdom node door: LSE Main Market, AIM, Aquis Stock Exchange. |
| `mcp.au-cm-kg.ai` | Australia node door: ASX, NSX (TMX Australia awaits a machine-readable list). |
| `mcp.capitalmarketsknowledgegraph.ai` | Global door: routes by identifier to the node that holds the name. `list_nodes` names the live nodes with their record counts; GB ISINs and LSE / AIM / Aquis tickers resolve to uk-cm-kg, CA ISINs and TSX / TSXV / CSE / Cboe tickers to ca-cm-kg, AU ISINs and ASX / NSX tickers (`BHP.AX`, `ASX:BHP`, `NSX:BCT`) to au-cm-kg. A name listed on two nodes (BHP on LSE and ASX) returns both. |

Read-only. No auth. Public-record only: no prices, quotes or licensed market data. Machine surfaces: no forward in front of any host, ever.

## Surfaces
- `POST /mcp` — Streamable HTTP MCP, JSON-RPC 2.0, stateless (no session id needed). `GET /mcp` answers 405 (no server-initiated stream).
- `GET /` short human page · `GET /facts.json` the door's facts (node, as_of, counts, tools; the global door lists every node's counts) · `GET /llms.txt` · `GET /nodes.json`
- `GET /record/<EXCHANGE>/<TICKER>` on a node host, or `GET /record/<node>/<EXCHANGE>/<TICKER>` on any host, the CMR v0 record · `GET /events/…` likewise, `?since=YYYY-MM-DD&cursor=0&limit=50`. Exchanges: `TSX`, `TSXV`, `CSE`, `CBOE-CANADA` (ca-cm-kg); `LSE`, `AIM`, `AQSE` (uk-cm-kg); `ASX`, `NSX` (au-cm-kg).
- Every response carries `X-CMR-Node`, `X-CMR-As-Of`, `X-CMR-Version`, `X-CMR-Source: public-record`, `X-CMR-Operator: Allooloo Technologies Corp.`, `X-CMR-Registry: io.github.allooloo/cm-kg`; HSTS.
- GET paths are edge-cached (records and events 1 h, facts and the page 5 min); MCP POST is `no-store`.
- Per-IP rate limit through the Workers rate-limiting binding: 600 requests per 60 s. No keys.

## Tools
resolve_issuer · get_record · list_events_since · list_aliases · list_nodes, each with a title and read-only / non-destructive / closed-world / idempotent annotations. Identifier parsing: ticker with or without exchange (`SHOP`, `TSX:SHOP`, `SHOP.TO`, `AUMB.V`, `CSE:AWR`, `SHEL`, `LSE:SHEL`, `SHEL.L`, `AIM:4BB`, `AQSE:DGQ`), ISIN, LEI, an exact legal name or a sourced alias, or a CMR key (`uk-cm-kg/LSE/SHEL`). A node host answers only for its node; the global door answers across nodes. An ambiguous ticker returns every match; the door never guesses.

## Store — the call
D1 and KV were both refused by the account token (`Authentication error` on create), so the door's store is **Workers Static Assets**, laid out per node since ORDER-010: `data/records/<node>/<EXCHANGE>/<TICKER>.json`, `data/events/<node>/<EXCHANGE>/<TICKER>.json`, plus one `index.json` across nodes (ticker, ISIN, LEI, alias, legal name → CMR keys), `facts.json` (per-node counts), `nodes.json`. Two nodes = about 12,800 files; three nodes (ORDER-013) = 16,537 files, against the static-assets cap of 20,000 files per version (ORDER-010 Part A step 4: at the cap, STOP and report; that is the D1 token decision). The Worker reads assets through the `ASSETS` binding with `run_worker_first`, so raw asset paths are never exposed.

## Data and the loader rail
`CM-KG\RAILS\door\load_nodes.py` (node-generic; replaces `ca-door\load.py`) reads the **confirmed** outputs only — `CM-KG\ISSUERS\<cc>-issuers.xlsx` and `CM-KG\DISCLOSURE\events\<cc>-events.jsonl` for every node with a workbook — and writes `data/`. Idempotent on (node, exchange, ticker). Re-run after every weekly sweep (`ca-weekly` / `uk-weekly` tasks do so), then `wrangler deploy` here (only changed assets upload). Record shape: `CM-RECORD\cmr-v0.md`. Blank stays blank: a field with no value is present with `value: null` and its reason from Gaps. No `signature` key exists; it is omitted, not stubbed. Proof: `CM-KG\RAILS\door\prove.py <host>` (direct JSON-RPC, then the Claude API MCP connector).

## Deploy
`wrangler deploy` from this folder with `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` in the environment (read from `AGENT KEYS\cloudflare.txt` at launch, never printed). Custom domains are attached at account level (`PUT /accounts/{id}/workers/domains`) because the token lacks zone Workers Routes; wrangler's routes step prints an error that is cosmetic. Registry listing: `server.json` (io.github.allooloo/cm-kg); v0.2.0 (two nodes) is published; v0.3.0 with `nodes_live` ca, uk, au is staged in the file (ORDER-013) and published only on the CEO's go (public channel rule).
