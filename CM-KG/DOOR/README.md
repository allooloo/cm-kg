# CM-KG door — `cm-kg-door` (Cloudflare Worker)

One codebase, deployed to two hosts (ORDER-005, September 10 2026):

| Host | Scope |
|---|---|
| `mcp.ca-cm-kg.ai` | Canada node door: TSX, TSXV, CSE, Cboe Canada. English default. |
| `mcp.capitalmarketsknowledgegraph.ai` | Global door: routes by identifier to the node that holds the name. Live today: Canada only; `list_nodes` says so. |

Read-only. No auth. Public-record only: no prices, quotes or licensed market data. Machine surfaces: no forward in front of either host, ever.

## Surfaces
- `POST /mcp` — Streamable HTTP MCP, JSON-RPC 2.0, stateless (no session id needed). `GET /mcp` answers 405 (no server-initiated stream).
- `GET /` short human page · `GET /facts.json` the door's facts (node, as_of, counts, tools) · `GET /llms.txt` · `GET /nodes.json`
- `GET /record/<EXCHANGE>/<TICKER>` the CMR v0 record · `GET /events/<EXCHANGE>/<TICKER>?since=YYYY-MM-DD&cursor=0&limit=50` paged events. Exchanges: `TSX`, `TSXV`, `CSE`, `CBOE-CANADA`.
- Every response carries `X-CMR-Node`, `X-CMR-As-Of`, `X-CMR-Version`, `X-CMR-Source: public-record`, `X-CMR-Operator: Allooloo Technologies Corp.`
- GET paths are edge-cached (records and events 1 h, facts and the page 5 min); MCP POST is `no-store`.
- Per-IP rate limit through the Workers rate-limiting binding: 600 requests per 60 s. No keys.

## Tools (descriptions verbatim from ORDER-005)
resolve_issuer · get_record · list_events_since · list_aliases · list_nodes. Identifier parsing: ticker with or without exchange (`SHOP`, `TSX:SHOP`, `SHOP.TO`, `AUMB.V`, `CSE:AWR`), ISIN, LEI, or a CMR key. An ambiguous ticker returns every match; the door never guesses.

## Store — the call
D1 and KV were both refused by the account token (`Authentication error` on create), so the door's store is **Workers Static Assets**: one JSON per record (`data/records/<EXCHANGE>/<TICKER>.json`), one per issuer's events (`data/events/…`), plus `index.json` (ticker, ISIN, LEI → CMR keys), `facts.json`, `nodes.json`. 9,643 files, ~43 MB. The Worker reads them through the `ASSETS` binding with `run_worker_first`, so raw asset paths are never exposed and every response goes through the header and cache rules. When the token gains a D1 scope the loader can target D1 without changing the tool surface.

## Data and the loader rail
`CM-KG\RAILS\ca-door\load.py` reads the **confirmed** outputs only — `CM-KG\ISSUERS\ca-issuers.xlsx` (4,820 rows, corporate and fund rows alike, security type carried) and `CM-KG\DISCLOSURE\events\ca-events.jsonl` (25,222 events) — and writes `data/`. Idempotent on (exchange, ticker). Re-run after every weekly sweep, then `wrangler deploy` here (only changed assets upload). Record shape: `CM-RECORD\cmr-v0.md`. Blank stays blank: a field with no value is present with `value: null` and its reason from Gaps. No `signature` key exists; it is omitted, not stubbed.

## Deploy
`wrangler deploy` from this folder with `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` in the environment (read from `AGENT KEYS\cloudflare.txt` at launch, never printed). Custom domains are attached at account level (`PUT /accounts/{id}/workers/domains`) because the token lacks zone Workers Routes; wrangler's routes step prints an error that is cosmetic. Not listed on any registry, connector directory or allooloo.io in this order.
