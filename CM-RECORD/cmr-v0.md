# Capital Markets Record — CMR v0 (draft)

Allooloo Technologies Corp. · written under ORDER-005, September 10 2026 · status: draft, unsigned

The CMR is one record per listed company, keyed on ISIN, ticker and LEI. It is versioned and sourced; a record is superseded, never deleted. Every identity field names the registry it came from or the engine that read it, and carries a state. Blank stays blank: a field with no value is present with `value: null` and the reason the sweep recorded, never dropped.

## Key
`cmr` = `<node>/<exchange>/<ticker>` — for the Canada node: `ca-cm-kg/TSX/SHOP`, `ca-cm-kg/TSXV/AUMB`, `ca-cm-kg/CSE/AWR`, `ca-cm-kg/CBOE-CANADA/CYB`. Exchange segments are upper-case; spaces become hyphens. The same issuer listed on two exchanges is two records; `resolve_issuer` returns both and never guesses.

## Shape
```json
{
  "cmr": "ca-cm-kg/TSX/SHOP",
  "node": "ca-cm-kg",
  "as_of": "2026-09-10",
  "version": 1,
  "identity": {
    "name":           { "value": "…", "source_url": "…", "read_by": "…", "state": "sourced" },
    "ticker":         { … }, "exchange": { … }, "security_type": { … },
    "isin":           { … }, "lei": { … }, "sector": { … }, "jurisdiction": { … },
    "transfer_agent": { … }, "auditor": { … }, "newswire": { … },
    "hq_city":        { … }, "hq_region": { … }, "tier": { … },
    "sedar_profile":  { … },
    "sedi_link":      { "value": "…", "source_url": "", "read_by": "constructed …", "state": "unverified" }
  },
  "aliases": [ { "value": "CPKC", "source_url": "https://www.newswire.ca/news/cpkc/", "read_by": "newswire.ca company page (found by Perplexity (agent))" } ],
  "events_url": "https://mcp.ca-cm-kg.ai/events/TSX/SHOP",
  "gaps": [ { "field": "lei", "reason": "…" } ]
}
```
A field with no value: `{ "value": null, "source_url": null, "read_by": null, "state": null, "reason": "<the Gaps line>" }`.

## Field states
- `sourced` — one source read; source URL and reader on the field.
- `filled` — written by a lab read or adjudication (`adjudicated by Claude`, `read by Gemini`, …); source cited.
- `confirmed` — two independent sources agree; both cited (`second_source_url`, `second_read_by` when present).
- `conflict` — the second source disagreed and adjudication did not settle it; the value is blank and the reason is on the field.
- `unverified` — constructed from a pattern the registry would not let a machine fetch (SEDI today).

## Versioning
`version` is an integer starting at 1 on the first signed-off sweep of the node. A weekly Fill + Confirm run that changes any identity field, alias or state bumps the version and keeps the prior record retrievable (`get_record` with `version`). The monthly re-harvest bumps every record it changes. Nothing is deleted.

## Events
Events are not part of the record body; the record carries `events_url`, a paged endpoint: `GET /events/<exchange>/<ticker>?since=YYYY-MM-DD&cursor=<n>&limit=<n>`. Each event: `date`, `event_type` (newswire_release · financial_statement · agm_record_date · early_warning · corporate_action · halt_resume · exchange_bulletin), `title`, `wire`, `source`, `url`, `read_by`, `state`, `detail`, and where a lab read the release: `period_end`, `statement_date`, `auditor_named`, `going_concern`, `extract_read_by`. No event without a URL and a date.

## Signature
Absent in v0. The `signature` key is omitted entirely until cm-record signing exists (keys, kid, canonicalisation, and the verifier at cm-record.org). Never stubbed.

## Headers (every door response)
`X-CMR-Node` · `X-CMR-As-Of` · `X-CMR-Version` · `X-CMR-Source: public-record` · `X-CMR-Operator: Allooloo Technologies Corp.`

## Out of scope, by rule
Prices, quotes, volumes, index membership, licensed market data. Anything behind a login. Inferred or guessed fields.
