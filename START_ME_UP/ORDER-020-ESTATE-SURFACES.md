# START_ME_UP \ ORDER-020-ESTATE-SURFACES.md

ORDER-020 — CORPORATE + PRODUCT SURFACES, STATUS, RADAR, WARMING, FILINGS
Owner: Allooloo Technologies Corp. Cut: 2026-09-12 (CEO go, all items ride together).
Runs after ORDER-019 reports. Fly-by-wire: shape calls are CC's, logged in START_ME_UP\ORDER-020-BUILD-LOG.
Rule One holds everywhere except the four approved end-of-scope deletions (separate paste).

---

## 0 Record-grade — the universal page standard (cite this section on every surface order from here on)

0.1 The page is a record. Every surface carries `as of` (YYYY-MM-DD) and a version; prior renders go to the pond; a reader can see what a page said on any date.
0.2 Text, tables, code, numbers. No hero images, no stock photography, no illustration. The one mark, top left. Facts in tables with a source column; machine calls in code blocks; numbers live from the doors. A block that cannot show a source does not go on the page.
0.3 Zero third-party scripts. No analytics tags, no CDN fonts, no chat widget, no cookie banner. Cloudflare edge logs are the analytics. Stated on the No-cookies page.
0.4 Speed as a number. Under 50 KB per page, one CSS file, no JavaScript except the form honeypot. Served from the edge.
0.5 Security headers as content. Strict CSP, HSTS, no inline scripts; the headers listed in the machine kit; `/.well-known/security.txt` on every zone.
0.6 One nav, one form, one footer, identical on every surface. Only the record changes page to page.
0.7 Two colours, one type stack (tokens in §1). The mark carries the brand; the layout carries none.
0.8 Machine twin on every page: llms.txt, facts.json, Agent Card where one exists, WebSite JSON-LD (name "Allooloo"), og:site_name, self-canonical, the favicon set. Same register for the crawler as for the person.
0.9 Copy register: machine instructions — numbered clauses, `field: value`, enumerations. No adjectives that are not measurements, no second person, no marketing vocabulary, no first-claims, no superlatives, no currency codes, no firm names other than the operator. "confirmed" never "signed".
0.10 Precedent: Berkshire Hathaway's site, EDGAR, TheStreet — unchanged for decades, trusted because nothing on the page persuades.

---

## 1 Tokens

```
--navy   #14213D   headings, body text, the mark
--green  #0B6E4F   links, the LIVE pill, the accent arc
--ink    #3A4256   secondary text
--muted  #6B7280   captions, source column, as-of lines
--rule   #D9DDE6   table and section rules (hairline)
--tint   #F3F5F9   table header band, code background
--paper  #FFFFFF   page
--mono   ui-monospace, SFMono-Regular, Menlo, Consolas
--sans   system-ui, -apple-system, Segoe UI, Roboto
```
Identifiers, tickers, ISINs, hostnames and page H1s in mono navy. State pill: green/white when live; navy/white when draft or Width 0. Links green, underline on hover only. No third colour anywhere.

Kicker line, top left above the mark, every surface:
`Microsoft AI Cloud Partner · Microsoft Azure · eleven regions, in-country`

---

## 2 Nav (nine tabs, every surface)

```
HOME        allooloo.io
Trades      agentic-trades.ai
ASK         agentic-ask.ai
Coverage    agentic-coverage.ai
ESG         agentic-esg.ai
Issuers     agentic-issuers.ai
Disclosure  agentic-disclosure.ai
Registries  agentic-registries.ai
RADAR       agentic-radar.ai
```
The 24 .com/.org/.io twins never appear in the nav. Node surfaces carry the same bar.

---

## 3 Footer (one row, every surface, © last)

```
Support · Status · Terms of Use · Privacy · Report a Security Issue · No cookies · llms.txt · Microsoft AI Cloud Partner · © 2026 Allooloo Technologies Corp.
```
- Support → developers@allooloo.ai
- Status → allooloo.io/status (§6)
- Terms of Use, Privacy → two record-grade pages, `as of` dated (copy: CEO supplies or Claude drafts on request; legal@allooloo.ai signs)
- Report a Security Issue → /.well-known/security.txt + one page
- No cookies → one-paragraph page: no third-party scripts, no trackers, edge logs only
- llms.txt → the machine kit
Below the row, one line: the eleven regions by name, in-country.

---

## 4 allooloo.io — the thirteenth surface (re-cut)

4.0 Order of the page (CEO ruling Sept 12 2026: scope and scale lead; no sample at the top — market participants do not need an example, they need the size of the dataset):
    head → H1 → scale block → reason-for-being → products (eight lines) → twelve-node table (live) → four licence shapes → engines and duties → Proof → contact.
4.0.1 Head of record:
      <title>AI Agents · MCP + A2A · Capital Markets Knowledge Graph — Allooloo</title>
      meta: "{{issuers}} listed companies, {{events}} dated disclosures, eleven markets served in-country. Every field sourced and read-dated. MCP and A2A."
      H1: Every listed company in eleven markets, as a record an agent can call.
4.0.2 Scale block, directly under the H1, five live numbers and nothing else:
      {{issuers}} listed companies · {{events}} dated disclosures, trailing twelve months · 11 markets · 11 Azure regions · served in-country · 100% fields carrying source URL and read date · {{last_drop}} last drop
4.0.3 Reason-for-being paragraph of record (first sentence names the two paying markets; the rest is the depth behind them):
      "Allooloo builds the Capital Markets Knowledge Graph for the dealers, brokers and wealth platforms of Toronto and London, and serves it from eleven markets: one record per listed company on the exchanges of Canada, the United States, the United Kingdom, France, the Netherlands, Switzerland, Germany, Australia, Singapore, Japan and Korea, with Hong Kong as a beacon. Every field carries the registry or filing it came from and the date it was read. Records are stored and served in the issuer's own jurisdiction; an apex router holds an index and forwards, nothing more. Agents call it over MCP and A2A; a desk, a watchlist, an ESG slice, an issuer record, the disclosure trail, a registry of agents and a live numbers page are built on it. Public record only. No prices, no quotes, no licensed data."
4.1 The sample record is RETIRED from the hero (the Sept 10 Doman Building Materials draft). One link in Proof only — "what a record looks like" → a live `get_record` from the Canada door, rendered on its own page, for the reader who wants to see one after they know the scale.
4.2 Numbers everywhere on the page are live from `list_nodes`. The "4,820 in one session" line retires.
4.3 Strike outright: "1T+ datapoints", "50,000+ organizations", "Three regions" — not Allooloo figures.
4.4 "Twelve nodes, each a public registry and a door" → eleven doors, Hong Kong a beacon with a partner wanted. Say what is true.
4.5 Keep: the desk pitch, the KYP / product-governance paragraph, the four licence shapes, "Eight engines. Named duties. Human cut.", the form.
4.6 Contact block carries both addresses and the README line: "The agents that built this read their own mail: allooloo@hey.com."
4.7 `/radar` → 308 → agentic-radar.ai. `/received` not needed; Formspree redirects to the root.

---

## 5 Eight product pages — the .ai roots

5.0 TITLE RULE (CEO, Sept 12 2026 — "AI agent" is the top search term on the estate's own analytics): the phrase "AI agents" appears once in every <title>, once in every meta description, and once in every H1 where it is not forced, on all 21 surfaces (company, eight products, twelve nodes). Three grammars, first word fixed:
    Company   AI Agents · MCP + A2A · Capital Markets Knowledge Graph — Allooloo   (search phrase first; the company name is the part that clips)
    Nodes     <Country> Capital Markets Knowledge Graph for AI agents — <node-id>
    Products  Agentic <Product> for AI agents — <what it is>   (the search phrase inside the first 30 characters; the descriptor is what clips)
    Product titles of record:
      Agentic Trades for AI agents      — the product line
      Agentic ASK for AI agents         — ask about any listed company
      Agentic Coverage for AI agents    — a watchlist that reads the record
      Agentic ESG for AI agents         — sustainability disclosures as filed
      Agentic Issuers for AI agents     — your record, signed and live
      Agentic Disclosure for AI agents  — the trail, dated and sourced
      Agentic Registries for AI agents  — who may call, and what they did
      Agentic RADAR for AI agents       — the estate numbers
    The node <title> in NODE-SURFACES.md §6 is amended to this grammar.

(head blocks of record below; body in the nine-section spec form of NODE-SURFACES where a product has a door, otherwise Scope · What it is · Access · Provenance · Estate · Machine kit · Contact)

Each: `<title>` as given · H1 · one reason-for-being paragraph · then the sections. Live numbers from the doors wherever a number appears.

**agentic-trades.ai** — `Agentic Trades — the Allooloo product line`
H1: The data systems agents trade on.
> Agentic Trades is the family name for Allooloo's products: the Capital Markets Knowledge Graph and its eleven sovereign doors, the ASK desk, Coverage, ESG, Issuers, Disclosure, Registries and RADAR. One record per listed company, source and read date on every field, stored and served in the issuer's jurisdiction. This page is the map; each product has its own.
Body: the eight products, one line each, linked; the twelve nodes table (live); the four licence shapes.

**agentic-ask.ai** — `Agentic ASK — ask about any listed company`
H1: One question, one door, twelve markets.
> ASK is the desk over the Capital Markets Knowledge Graph. The identifier does the routing: a TSX name opens the Canada node, a Xetra name opens the German node. Default scope is the market the name belongs to; cross-border when it is the question. Every answer is a record with sources, never a summary. Runs at ask.allooloo.io.
Body: how routing works; what an answer contains; the KYP / product-governance duty line; link to the desk.

**agentic-coverage.ai** — `Agentic Coverage — a watchlist that reads the record`
H1: Every product on the shelf, watched weekly.
> Coverage is a firm's list of issuers held against the record: each sweep, what changed on every name — filings, results, holders, auditors, going-concern notes — dated and sourced. Built for the duty a dealer cannot decline: know every product on the shelf, continuously. Twelve markets, one list.
Body: what a coverage list is; what a weekly delta contains; the duty by jurisdiction (KYP, product governance, DDO, reasonable-basis suitability, product due diligence); access.

**agentic-esg.ai** — `Agentic ESG — the sustainability slice of the disclosure trail`
H1: What issuers disclosed on sustainability, as filed.
> ESG is the slice of the disclosure trail that carries sustainability, climate and governance filings — each event dated, typed and linked to the regulator's copy. No score, no rating, no interpretation: the filing itself, with its source. Twelve markets on one record.
Body: which event types; sources per market; what is not carried (scores, ratings); access.

**agentic-issuers.ai** — `Agentic Issuers — your record, signed and live`
H1: The record every dealer agent reads about your company.
> Issuers is the issuer side of the graph: a listed company's own record — legal name, identifiers, auditor, registrar, fiscal period, disclosure trail — as every dealer agent sees it, with the source on each field. Confirm it, correct it at the source, and it is live to every agent on the estate. Signing lands with cm-record.org.
Body: what an issuer record carries; how corrections work (at the source of record, never by request); the issuer licence shape; access.

**agentic-disclosure.ai** — `Agentic Disclosure — the trail as a product`
H1: Every disclosure, dated, typed, sourced. Twelve markets.
> Disclosure is the trail itself, offered as a product: per-node feed of what every issuer filed as it lands; jurisdiction exports of records and twelve-month trail; the provenance log — where each field came from, when it was read, what changed between drops; and the query log, kept in-region, of what a firm's agents asked and were answered. Public-record only; nothing a data licence could pull back.
Body: the four shapes; counts per node (live); the residency rule; access behind Registries.

**agentic-registries.ai** — `Agentic Registries — who may call, and what they did`
H1: The registry of agents on the estate.
> Registries is the security and confirms layer: which agents are known to the estate — identity, the Agent Card they present, what they are licensed to read, which nodes, until when, revoked or not — and the signed record of what they did: CMR signing, attestations, receipts. Eleven doors, one list. Registered once, known in every market.
Body: registration (the skill / email on-ramp); what a registration carries; what a receipt carries; revocation; state: gate not yet in service — stated flatly.

**agentic-radar.ai** — `Agentic RADAR — the estate numbers`
H1: The estate, live, on one page.
> RADAR is the numbers page: records and events per node, door response times, agent calls per door, sweep motion, provenance coverage, residency, registry state, machine surfaces, and the cost of the record. Every figure is a door, a log or a ledger; nothing quoted from a third party. radar.json beside it, free, no registration.
Body: §7 of this file.

---

## 6 Status — allooloo.io/status and /status.json

A Cloudflare Worker cron: every five minutes, one real `resolve_issuer` (the node's §2 example issuer) against each of the eleven doors, round-trip in ms written to KV.
Table: `node · region · state · last call · response ms · 24h median · last drop`. Hong Kong: beacon, partner wanted. `/status.json` for agents. Record-grade, no chart beyond a 24h line per node.
This is the probe RADAR widget 02 reads. One call per node per five minutes; no other polling anywhere.

---

## 7 RADAR — agentic-radar.ai widget index v1

```
01 The Record       issuers · events · nodes live · last drop — estate + per node (list_nodes)
02 The Doors        eleven doors: region · state · response ms · 24h median (from §6)
03 The Trail        events per node, trailing twelve months; weekly delta line (Numbers Log)
04 Calls            agent calls per door per day (edge logs); tool mix; markets asked
05 Geography        calls by region %, top markets
06 Motion           sweep line per node: drop landed · records changed · events added
07 Provenance       fields with source + read date: 100%; confirmed vs pending by node; Gaps count
08 Residency        eleven regions in-country; apex index only; no-fallback rule, with the map
09 Registry         MCP registry card version · Agent Cards published · skill state · filings (§9) as they land
10 Machine surfaces radar.json · status.json · llms.txt · facts.json · agent-card · openapi · sitemap — listed, fetchable
11 Cite · Embed     citation block · GET radar.json example · iframe embed · JSON/CSV export — free, no registration
12 Spend            Azure line and lab line by node, as reported
13 Broadcast        @allooloo_io · allooloo@hey.com
14 Contact          the form (Formspree) · developers@allooloo.ai
```
Head: mono `AGENTIC RADAR` · "The estate numbers · Allooloo Technologies Corp. · v1.0" · nine-tab nav · LIVE clock. Footer per §3. Nothing on this page is quoted from a third party.

---

## 8 Warming

Minimum replicas 1 on every regional door Container App (and the apex if it moves to Azure later). Consumption tier. Report the per-region line in the spend section. The Status 24h line is the proof the setting works.

---

## 9 Registry filings (one card, one description, same endpoints everywhere)

9.1 Azure API Center — register the eleven doors + apex as MCP servers in the Allooloo tenant.
9.2 Google — the enterprise MCP / agent catalogue listing for the apex and doors.
9.3 Anthropic — connector directory submission for the apex.
9.4 MCP registry — v0.11.0 published; bump on any door change.
9.5 GitHub MCP listing and A2A agent directories as they stabilise; same cards.
Card of record: title "Capital Markets Agents: MCP+A2A Canada"; description "Know every Canadian and UK issuer, agent-ready. Instantly. Provably. Eleven markets, in-country."; website capitalmarketsknowledgegraph.ai; remote mcp.capitalmarketsknowledgegraph.ai/mcp. HITL where a filing needs a human account: list it, continue.

---

## 10 Sweeps — RE-ARMED (CEO word, Sept 12 2026)

Weekly per node: harvest → immutable pond drop → regional store reload → list_nodes updates → surfaces re-render → one line to NODE-SURFACES.md NUMBERS LOG. Engine roles and reading order as ruled. Registry versions stage, never publish without CEO go. BUILD lock lifts; the standing spend line reports per sweep.

---

## 11 Report (one, at close)

Record-grade standard applied (surfaces count); allooloo.io re-cut live with the live hero record; eight product pages live with heads as given; nav and footer on every surface (count); Terms/Privacy/Security/No-cookies pages live; Status live with first 24h line; RADAR live with all fourteen widgets bound to live sources; warming applied per region with the spend line; filings state per registry with HITL list; first sweep line written per node; the four approved deletions confirmed by name.

---

## 12 Customer focus — Toronto and London (CEO reset, Sept 12 2026)

The estate is global depth; the sale is two cities. Nothing below changes the architecture; it changes what a buyer reads first.

12.1 Toronto.
    Buyer: investment dealers and wealth platforms under CIRO; the fund managers who feed them.
    Duty: KYP — every product on the shelf, known continuously, and the file that proves it.
    Pain: a 15-to-30-person data floor doing it by hand across TSX, TSXV, CSE and Cboe Canada.
    First product: Dealer MCP access to the Canada node + Coverage on their shelf.
    Proof they check first: served from Canada Central; public-record only; source and read date on every field.

12.2 London.
    Buyer: brokers, wealth managers and platforms under the FCA product governance rules (PROD); the compliance consultancies that serve them.
    Duty: know the product and its target market, and show your work.
    Pain: the same data floor across Main Market, AIM and Aquis, with RNS as the firehose.
    First product: Dealer MCP access to the UK node + Disclosure as the feed.
    Proof they check first: served from UK South; FCA NSM and Companies House as sources; nothing licensed on the wire.

12.3 What changes on the surfaces.
    - ca-cm-kg.ai and uk-cm-kg.ai: the duty line (12.1 / 12.2) and the buyer's first product sit above the fold, directly under the scale numbers, before section 1. Every other node page keeps the standard order.
    - allooloo.io: the scale block stays global; the first sentence of the reason-for-being names Toronto and London (4.0.3).
    - Registry card: unchanged — it already speaks to Canada and the UK with the eleven markets as the second beat.
    - agentic-coverage.ai and agentic-disclosure.ai: each opens with the city whose first product it is (Coverage → Toronto, Disclosure → London), then the other, then the rest.

12.4 What stays out of the pitch: engines, sovereignty architecture, agent philosophy. The buyer reads duty, shelf, proof, price. The depth argument (nine other doors, RADAR, product pages) sits behind the two sales, not in front of them.

12.5 Copy register unchanged (§0.9). The duty lines are regulatory terms, not marketing: KYP, PROD, product governance — the buyer's own words.
