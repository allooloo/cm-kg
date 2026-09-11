# ORDER-005 — Canada node MCP door
Date: Sept 10 2026 · Node: ca-cm-kg · Folder: C:\ALLOOLOO\CM-KG\ (repo allooloo/cm-kg) · Fly by wire.

## What it is
The first door. One MCP server codebase that serves the Capital Markets Knowledge Graph to any agent, built once,
deployed twice today: the Canada node door and the global door. Every later node is the same deploy pointed at its own data.
Read-only. No auth. Public-record only.

## Hosts (both must answer before this order closes)
- mcp.ca-cm-kg.ai — the Canada node: scoped to TSX / TSXV / CSE / Cboe Canada, English default.
- mcp.capitalmarketsknowledgegraph.ai — the global door: routes by identifier to whichever node holds the name;
  today that is Canada only, and list_nodes says so honestly.
Both are machine surfaces: no forward in front of them, ever. Streamable HTTP MCP at /mcp; GET / returns a short
human page and GET /facts.json the door's facts (node, as_of, counts, tool list). /llms.txt on each host.

## Data
Load from the confirmed outputs, not the raw:
- CM-KG\ISSUERS\ca-issuers.xlsx → one CMR per row (all 4,820; corporate and fund rows alike, security type carried).
- CM-KG\DISCLOSURE\events\ca-events.jsonl → events per issuer, paged.
Store on Cloudflare (D1 or KV — CC's call; note it in the README). Loader is a rail: CM-KG\RAILS\ca-door\load.py,
re-runnable after every weekly sweep, idempotent on (ticker, exchange).

## The record shape (CMR v0 — the spec draft lives at CM-RECORD\cmr-v0.md, written in this order)
{
  "cmr": "ca-cm-kg/<exchange>/<ticker>",
  "node": "ca-cm-kg", "as_of": "<date>", "version": <int>,
  "identity": { each field as { "value", "source_url", "read_by", "state" } — name, ticker, exchange, security_type,
                isin, lei, sector, jurisdiction, transfer_agent, auditor, newswire, hq_city, hq_region, tier,
                sedar_profile, sedi_link (state "unverified") },
  "aliases": [ { "value", "source_url", "read_by" } ],
  "events_url": "<paged endpoint>",
  "signature": absent — omit the key entirely until cm-record signing exists. Do not stub.
}
Blank stays blank: a field with no value is present with value null and its reason from Gaps, never dropped.

## Tools (identical on both doors; descriptions verbatim — they are what an agent reads to decide to call)
- resolve_issuer — "Find a listed company by ticker, ISIN or LEI and return its record summary, node and current version."
- get_record — "Return the full Capital Markets Record for an issuer, with per-field source, reader and state; optionally a prior version."
- list_events_since — "Return dated, URL'd disclosure events for an issuer (releases, bulletins, halts, corporate actions, statement and record dates) since a date."
- list_aliases — "Return the sourced trade and former names an issuer releases under."
- list_nodes — "Return the twelve market nodes and which are live."
Identifier parsing: ticker with or without exchange prefix (SHOP, TSX:SHOP, SHOP.TO), ISIN, LEI. Ambiguous ticker
across exchanges → return all matches, never guess.

## Response headers (every response, both doors)
X-CMR-Node · X-CMR-As-Of · X-CMR-Version · X-CMR-Source: public-record · X-CMR-Operator: Allooloo Technologies Corp.

## Deploy
- Cloudflare Workers on the same account as allooloo.io. FIRST confirm both zones (ca-cm-kg.ai, capitalmarketsknowledgegraph.ai)
  are in the account AGENT KEYS\cloudflare.txt authenticates; if not, STOP and report.
- Rate limit per IP, generous; no keys. Edge cache on GET paths; MCP POST uncached.
- No listing on any registry, connector directory, or on allooloo.io in this order. Doors first, listings after — separate go.

## Report
Both URLs answering · tool list as returned to a real MCP client (attach the door to Claude via the connector and call
list_nodes and resolve_issuer for SHOP, one TSXV name, one CSE name — paste the returned records) · p50 latency from
Toronto, London, Singapore · the CMR v0 spec file path · what is broken. Nothing else.

## Don't
- No auth, no write tools, no prices or market data.
- No forward in front of either host. No stubbed signature. No test harness before the roll.
- No reference to any other company's estate, code, or canon.
