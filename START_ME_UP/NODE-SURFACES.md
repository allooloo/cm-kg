# START_ME_UP \ NODE-SURFACES.md

Boot file for the twelve Capital Markets Knowledge Graph node surfaces and the weekly numbers motion.
Owner: Allooloo Technologies Corp. Cut: 2026-09-12 (CEO go). Read before any surface build or sweep.
Runs as ORDER-019 after ORDER-018 (Sovereign Estate) reports. Fly-by-wire: shape calls are CC's, logged in START_ME_UP\ORDER-019-BUILD-LOG.

---

## 0 Rules

0.1 Surfaces are front of house. The node is the machine: `mcp.<node>-cm-kg.ai` (MCP door) and `agent.<node>-cm-kg.ai` (A2A Agent Card). The surface tells a human or a crawler the node exists and hands them to it. It answers nothing itself.
0.2 One surface per node on `<node>-cm-kg.ai`. `.org` and `.com` 301 to `.ai`, path and query preserved. Self-referencing canonical on the `.ai`.
0.3 Copy is written as machine instructions: spec register, numbered clauses, `field: value` lines, enumerations. No narrative, no adjectives that are not measurements, no second person, no marketing vocabulary, no first-claims, no superlatives, no currency codes, no firm names other than the operator.
0.4 Counts and dates are live fields from that node's `list_nodes`. Never typed constants. Integers and `YYYY-MM-DD`.
0.5 The head block and section 6 are written per market. Under 40% shared text between any two node pages. Report the pairwise figure once; do not build a rig for it.
0.6 Section 2 example is a real issuer that market knows, with the real wire response captured from that door at build. Never the same issuer on two pages.
0.7 Sections 4, 5, 6 are per-node fact from that node's rail README. The Gaps note is carried verbatim. Known gaps are stated, never hidden.
0.8 "confirmed", never "signed". British spelling on uk. Japanese and Korean titles carried as published, never translated.
0.9 Hong Kong renders the local-partner variant. United States renders the partial until its door answers. Broken is broken; no "coming soon".
0.10 Sweeps write the NUMBERS LOG. Nothing else in this file changes without CEO word.
0.11 Nothing of ours is deleted or overwritten. New output beside old.

---

## 1 Structure (fixed order, all nodes)

```
head   <title> · <meta description> · H1 · reason-for-being paragraph
1  Scope
2  Access
3  Residency
4  Provenance
5  Known gaps
6  Market particulars
7  Estate
8  Machine kit
9  Contact  (incl. the form, §3 below)
```

Section 6 is where the pages differ by design: exchange tiers and segments, filing language, regulator and register names, register key type, fiscal-year convention, identifier forms the door accepts.

---

## 2 Variation rule

Twelve domains carrying one template with the country swapped is what a search engine groups as duplicate. Per node:

- H1 and reason-for-being are written for that market: different lead fact, different sentence order, its own numbers. Canada leads with four exchanges; Japan with filings carried in Japanese; Korea with DART; Germany with the segment gap stated up front; Hong Kong with the partner wanted; France and the Netherlands with ISIN as the key.
- Section 2 example: real issuer, real wire response, per node.
- Sections 4, 5, 6: per-node fact from the README.
- Section 7 lists the other eleven, so it differs on every page by construction.
- Each zone carries its own `<title>`, `<meta>`, `facts.json` and `llms.txt` with that node's numbers.

Target: under 40% shared text between any two node pages.

---

## 3 Contact form (every surface the estate Worker serves)

Section 9 on every node page, and the contact block on allooloo.io and the apex, carries one form:

```
action    https://formspree.io/f/moeqzgll      method POST
fields    email (required) · message (required)
hidden    _subject = "<hostname> contact"
hidden    _gotcha  (honeypot)
hidden    _next    = https://allooloo.io
```

Same markup everywhere, rendered by the Worker. `<hostname>` in `_subject` is the only per-site value. No captcha, no JS dependency. The two mail addresses are printed beside the form.

Formspree settings on `moeqzgll` (CEO): redirect → https://allooloo.io · notifications → developers@allooloo.ai.

---

## 4 Live fields

From that node's `list_nodes`, on every render:

| field | used in |
|---|---|
| issuer count | 1.4, meta description, every other page's §7 row |
| event count | 1.5, meta description, every other page's §7 row |
| drop date | 1.7 |
| last sweep date | 1.7 (once sweeps are armed) |

The surfaces move when the numbers move. No re-cut per sweep.

---

## 5 Weekly motion (armed only on CEO word, after ORDER-018 reports)

Per node, weekly:

```
harvest → new immutable pond drop → regional store reload
→ list_nodes reflects new counts and drop date
→ every surface in the estate updates on next render
→ one line appended to NUMBERS LOG (§9): node · date · records · events · delta
```

The log is the perpetual-motion record. Nothing else needs writing.

---

## 6 Reference page — uk-cm-kg.ai (the page of record; other nodes are built from §7, not copied from this)

### head

```
<title>United Kingdom Capital Markets Knowledge Graph — uk-cm-kg</title>
<meta name="description" content="Agentic capital markets record: {{live_issuer_count}} UK issuers, {{live_event_count}} dated disclosures, every field sourced and read-dated. Served from London over MCP and A2A.">
<link rel="canonical" href="https://uk-cm-kg.ai/">
```

**H1** — Every listed company in the United Kingdom, as a record an agent can call.

> This node serves {{live_issuer_count}} issuer records and {{live_event_count}} dated disclosure events for the London Stock Exchange Main Market, AIM and Aquis. An agent resolves an issuer by ticker, ISIN, LEI or name; reads its record; lists the names it has traded under; pulls every disclosure since a date; and asks which of the twelve nodes holds any other market. Access is MCP (streamable-http) and A2A, five tools, answers scoped to the United Kingdom. Every field carries its source — FCA National Storage Mechanism, Companies House, LSE RNS — and the date it was read. Records are stored and served from London; the apex router holds an index and forwards, nothing more. Known gaps are stated. Market particulars, machine kit, registry entry and contact follow.

### 1 Scope

1.1 Jurisdiction: United Kingdom
1.2 Node ID: `uk-cm-kg`
1.3 Coverage: London Stock Exchange Main Market; AIM; Aquis
1.4 Issuer records: `{{live_issuer_count}}`
1.5 Dated disclosure events: `{{live_event_count}}`
1.6 Disclosure period: trailing twelve months
1.7 Drop date: `{{live_drop_date}}`
1.8 Operator: Allooloo Technologies Corp.
1.9 Counts and drop date are populated from the node. Counts render as integers. Dates render as `YYYY-MM-DD`.

### 2 Access

2.1 MCP endpoint: `https://mcp.uk-cm-kg.ai/mcp`
2.2 Transport: `streamable-http`
2.3 Agent Card: `https://agent.uk-cm-kg.ai`
2.4 Agent protocol: A2A
2.5 Answer scope: `uk-cm-kg` only
2.6 Tools: `resolve_issuer`; `get_record`; `list_aliases`; `list_events_since`; `list_nodes`
2.7 Accepted identifiers: ticker (`LSE:SHEL`, `SHEL.L`, `AIM:4BB`, `AQSE:DGQ`); ISIN; LEI; legal name; sourced alias.

2.8 Request:

```json
{ "tool": "resolve_issuer", "arguments": { "identifier": "LSE:SHEL" } }
```

2.9 Response (captured from the wire 2026-09-12):

```json
{
  "matches": [
    {
      "cmr": "uk-cm-kg/LSE/SHEL",
      "node": "uk-cm-kg",
      "version": 1,
      "as_of": "2026-09-11",
      "name": "SHELL PLC",
      "ticker": "SHEL",
      "exchange": "LSE Main Market",
      "security_type": "Corporate",
      "isin": "GB00BP6MXD84",
      "lei": "21380068P1DRHMJ8KU70",
      "sector": "Oil, Gas and Coal [601010]",
      "event_count": 408,
      "events_url": "https://mcp.uk-cm-kg.ai/events/LSE/SHEL",
      "record_url": "https://mcp.uk-cm-kg.ai/record/LSE/SHEL"
    }
  ],
  "matched_by": "ticker",
  "ambiguous": false,
  "nodes_asked": ["uk-cm-kg"]
}
```

### 3 Residency

3.1 Storage region: Azure UK South (London)
3.2 Serving region: Azure UK South (London)
3.3 Apex router: `mcp.capitalmarketsknowledgegraph.ai`
3.4 Apex content: index only
3.5 The apex router forwards requests to the jurisdictional node.
3.6 No record body leaves the jurisdiction.
3.7 No-fallback rule: records are not served from another jurisdiction when this node is unavailable.

### 4 Provenance

4.1 Sources of record: FCA National Storage Mechanism; Companies House; LSE RNS.
4.2 Field-class source mapping: `{{UK_README_FIELD_SOURCE_MAPPING}}`
4.3 Source URL: carried on every field.
4.4 Read date: carried on every field.
4.5 Read-date format: `YYYY-MM-DD`.
4.6 Record `as_of` and field read dates remain separate fields.
4.7 Every field carries source URL and read date; none is served without both.
4.8 Confirmed: the field as read from its source of record.
4.9 Signed: reserved for CMR signing; not yet in service. Not used on this node.

### 5 Known gaps

5.1 `{{UK_README_GAPS_NOTE_VERBATIM}}`
*(build note, stripped at render: insert the UK rail README Gaps note verbatim before release)*

### 6 Market particulars

6.1 Exchange tiers: LSE Main Market (FCA listing categories); AIM; Aquis Stock Exchange (Access, Apex).
6.2 Filing language: English.
6.3 Regulator: Financial Conduct Authority. Exchange: London Stock Exchange Group; Aquis Exchange.
6.4 Corporate register: Companies House. Register key: company number.
6.5 Disclosure channel: LSE RNS; FCA National Storage Mechanism.
6.6 Fiscal-year convention: set per issuer; carried as filed.
6.7 Identifier forms accepted by the door: `LSE:SHEL` · `SHEL.L` · `AIM:<code>` · `AQSE:<code>` · ISIN (`GB…`) · LEI · legal name · sourced alias.
6.8 Auditor, registrar and going-concern note: carried from the annual report as filed.

### 7 Estate

7.1 `ca-cm-kg` · Canada Central · `https://mcp.ca-cm-kg.ai/mcp` · `{{ca_records}}` records
7.2 `us-cm-kg` · East US · `https://mcp.us-cm-kg.ai/mcp` · `{{us_records}}` records
7.3 `fr-cm-kg` · France Central · `https://mcp.fr-cm-kg.ai/mcp` · `{{fr_records}}` records
7.4 `nl-cm-kg` · West Europe · `https://mcp.nl-cm-kg.ai/mcp` · `{{nl_records}}` records
7.5 `ch-cm-kg` · Switzerland North · `https://mcp.ch-cm-kg.ai/mcp` · `{{ch_records}}` records
7.6 `de-cm-kg` · Germany West Central · `https://mcp.de-cm-kg.ai/mcp` · `{{de_records}}` records
7.7 `au-cm-kg` · Australia East · `https://mcp.au-cm-kg.ai/mcp` · `{{au_records}}` records
7.8 `sg-cm-kg` · Southeast Asia · `https://mcp.sg-cm-kg.ai/mcp` · `{{sg_records}}` records
7.9 `jp-cm-kg` · Japan East · `https://mcp.jp-cm-kg.ai/mcp` · `{{jp_records}}` records
7.10 `kr-cm-kg` · Korea Central · `https://mcp.kr-cm-kg.ai/mcp` · `{{kr_records}}` records
7.11 `hk-cm-kg` · Width 0 · no endpoint · local partner wanted · `{{hk_records}}` lines

### 8 Machine kit

8.1 Machine instructions: `/llms.txt`
8.2 Facts: `/facts.json`
8.3 Agent Card: `https://agent.uk-cm-kg.ai`
8.4 Registry: `registry.modelcontextprotocol.io` · entry `io.github.allooloo/cm-kg`

### 9 Contact

9.1 developers@allooloo.ai — contact of record
9.2 allooloo@hey.com — the agents that built this read their own mail
9.3 Form: §3 of this file, rendered here.

---

## 7 Nodes (per-node inputs; "(README)" = taken verbatim from that node's rail README at build)

| node | country | region | coverage | sources of record | §2 example | key | notes |
|---|---|---|---|---|---|---|---|
| ca | Canada | Canada Central | TSX, TSXV, CSE, Cboe Canada | (README) | `TSX:SHOP` | ticker | four exchanges lead the H1 |
| us | United States | East US | NYSE, Nasdaq, NYSE American | EDGAR (README) | set when door answers | ticker | partial page until door answers |
| uk | United Kingdom | UK South | LSE Main Market, AIM, Aquis | FCA NSM, Companies House, LSE RNS | `LSE:SHEL` | ticker | reference page, §6 above |
| fr | France | France Central | Euronext Paris, Euronext Growth | (README) | `XPAR:FR0000120271` | ISIN | FIRDS rosters carry no symbol |
| nl | Netherlands | West Europe | Euronext Amsterdam | (README) | `AMS:NL0000009165` | ISIN | FIRDS rosters carry no symbol |
| ch | Switzerland | Switzerland North | SIX Swiss Exchange | (README) | `NESN.SW` | ticker | |
| de | Germany | Germany West Central | Frankfurt / Xetra | (README) | `SAP.DE` | ticker | Regulated Market vs Scale segment blank — state up front |
| au | Australia | Australia East | ASX | (README) | `ASX:BHP` | ticker | |
| sg | Singapore | Southeast Asia | SGX | (README) | `D05.SI` | ticker | English filings only |
| jp | Japan | Japan East | TSE Prime, Standard, Growth, PRO; REITs | JPX, EDINET (README) | `7203.T` | code | titles in Japanese; PRO Market 187 lines no EDINET filer |
| kr | South Korea | Korea Central | KOSPI, KOSDAQ, KONEX | KIND, DART (README) | `005930.KS` | code | titles in Korean; 43 KIND lines share a code |
| hk | Hong Kong | East Asia (config only) | HKEX Main Board, GEM, REITs | HKEX list, GLEIF (README) | — | — | Width 0 · no door · local partner wanted |

---

## 8 Report (ORDER-019 close)

Twelve URLs live · per-node example identifier used · pairwise shared-text figure · live-field bindings confirmed · form posting confirmed on one node and allooloo.io · NUMBERS LOG seeded with the current drop per node.

---

## 9 NUMBERS LOG

`node · date · records · events · delta`

*(seeded by ORDER-019; one line per sweep per node thereafter)*

```
ca-cm-kg · 2026-09-10 · 4820 · 25222 · seed (ORDER-019; first sweep line will carry the delta)
us-cm-kg · 2026-09-12 · 7710 · 1872343 · seed (ORDER-019; first sweep line will carry the delta)
uk-cm-kg · 2026-09-11 · 1570 · 128393 · seed (ORDER-019; first sweep line will carry the delta)
fr-cm-kg · 2026-09-11 · 712 · 9999 · seed (ORDER-019; first sweep line will carry the delta)
nl-cm-kg · 2026-09-11 · 123 · 2707 · seed (ORDER-019; first sweep line will carry the delta)
ch-cm-kg · 2026-09-11 · 829 · 1385 · seed (ORDER-019; first sweep line will carry the delta)
de-cm-kg · 2026-09-11 · 3436 · 35403 · seed (ORDER-019; first sweep line will carry the delta)
au-cm-kg · 2026-09-11 · 1874 · 124300 · seed (ORDER-019; first sweep line will carry the delta)
sg-cm-kg · 2026-09-11 · 639 · 3510 · seed (ORDER-019; first sweep line will carry the delta)
jp-cm-kg · 2026-09-12 · 3964 · 39274 · seed (ORDER-019; first sweep line will carry the delta)
kr-cm-kg · 2026-09-12 · 2802 · 143297 · seed (ORDER-019; first sweep line will carry the delta)
hk-cm-kg · 2026-09-12 · not served (Width 0) · none · seed (ORDER-019; no door, no sweep until a local partner)
nl-cm-kg · 2026-09-11 · 123 · 2742 · records +0 · events +35 (sweep 2026-09-12)
```

