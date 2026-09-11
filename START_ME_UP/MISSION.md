# MISSION — Agentic Capital Markets Global Desk
Allooloo Technologies Corp. · opened Sept 10 2026 · CEO: Matthew Keddy

## What we are building
The Capital Markets Knowledge Graph (CM-KG), served live to AI agents over MCP, and the
Agentic Capital Markets Global Desk on top of it. One desk, twelve sovereign nodes.

## The object
CMR — Capital Markets Record. One signed, versioned record per listed company, keyed on
ISIN / ticker / LEI. Superseded never deleted. Every field carries which lab read it.
Spec lives at cm-record.org; resolver at cm-record.ai; twin at cm-record.io.

## The wedge
Dealers carry a legal duty to know every product they shelve, continuously
(Canada: KYP, NI 31-103; UK: product governance; US: reasonable-basis suitability;
AU: DDO; SG: MAS product due diligence; EU: MiFID II product governance; CH: FinSA).
Today that is PDFs and analyst hours. A signed, current CMR over MCP discharges it.

## The estate (all owned — see COMPANY RECORDS\Allooloo_Domains_Master.xlsx, the single master; versioned copies live in CM-KG\POND\estate\domains\)
- capitalmarketsknowledgegraph.ai — the graph; mcp.capitalmarketsknowledgegraph.ai is the door
- cm-kg.org standard · cm-kg.io twin · cm-kg.ai/.com brand
- cm-record.org/.ai/.io/.com — the CMR
- Twelve nodes, each .org (registry) / .ai (door) / .com (brand):
  ca us uk sg au ch de jp hk fr nl kr
- allooloo.io — corporate site (allooloo.ai forwards here); ask.allooloo.io — the desk

## Build order — nodes
1 Canada · 2 UK · 3 Australia · 4 Singapore · 5 Switzerland + Germany ·
6 France + Netherlands · 7 Hong Kong + Japan + Korea · 8 United States LAST.

## Build order — widths (each width ships on its own)
- Width 0 Identity: every listed company per node — name, ticker, ISIN, LEI, exchange,
  tier, sector, incorporation, transfer agent, auditor, filing agent, newswire of habit,
  registry links. Output: CM-KG\ISSUERS\<country>-issuers.xlsx, then one CMR per issuer.
- Width 1 Disclosure: filings index, material changes, statement dates, AGM/record dates,
  halts/resumes, insider and early-warning filings — the fact, date, and location, not the document.
- Width 2 Edges: insiders across boards, holders across names, shared auditors and
  transfer agents, parent/subsidiary, dual listings across nodes, sector peers.
- Width 3 Reads: per-filing extracted facts; six labs read, one adjudicates, human cuts.
Deliberately out: prices, quotes, tick, index data, analyst estimates.

## Pipeline (one shape, all nodes)
Hunter (Tavily + Perplexity harvest) → issuers workbook → CMR minted + signed →
node .org publishes → graph indexes → desk + mcp. doors serve.
Widths 0–1 refresh daily; Width 2 weekly; Width 3 on each new filing.

## The orchestra — eight engines, named duties
- Claude (Opus 5): reader of record, CMR schema, adjudication, equipped reads
- ChatGPT (Responses API, Batches): structured extraction at scale, second opinion
- Google Gemini: long-context filing reads
- Perplexity (Agent API): grounded cold reads; Search API as harvest
- Grok 4.6: real-time newswire / halt / resume signal
- Mistral: EU-node readers (fr de nl ch), Document AI on scanned filings
- Tavily: general web search layer
- Cloudflare: the network — Workers, Workers AI embeddings, edge cache, every door

## The desk
One door (ask.allooloo.io), twelve corpora. The identifier routes: a TSX name opens
ca-cm-kg only; a Xetra name opens de-cm-kg, in German if asked in German.
Default scope is the node the identifier belongs to; the world is on request.

## Canada node — registries and regulators addressed
SEDAR+ · SEDI · NRD · CSA · CIRO · OSC / BCSC / AMF / ASC · TSX · TSXV · CSE ·
Cboe Canada · CDS · Computershare / TSX Trust / Odyssey Trust ·
Canada Newswire / Newsfile / GlobeNewswire / Business Wire / Accesswire

## Contract shapes (licence only — no services, ever)
1 Dealer MCP access licence · 2 Issuer record licence · 3 KG API licence · 4 Node operator licence.
Close order: issuer record → dealer MCP → KG API → node operators.

## Naming locked Sept 10 2026
Product: AI ASK ("AI assistant ask" in copy). Positioning: Agentic Capital Markets Global Desk.
Masthead register: "2027, today." No regulator's vocabulary in product names.
Never a name with I or L in any address.

## Dated items (plan, don't rush)
Perplexity Sonar retires Sept 27 2026 (Agent API in use). Google console MFA required by Oct 20 2026.
