# ORDER-002 — allooloo.io corporate site, ground-up
Date: Sept 10 2026 · Folder: C:\ALLOOLOO\SITE\ · Fly by wire.

## What it is
The corporate site of Allooloo Technologies Corp., built new for the agentic era. Two readers from
the first line: a banker on a phone, and an agent on the wire. One source, one deploy, on Cloudflare.
allooloo.ai stays live and untouched until the CEO separately orders the forward.

## Design direction (deliberate — not the defaults)
- Subject vernacular: the record, the register, the filing, the tape. The site reads like a signed record, not a SaaS landing page.
- One memorable element: the hero is a real Capital Markets Record, rendered — pick one corporate issuer from
  CM-KG\ISSUERS\ca-issuers.xlsx with the fullest row (name, ticker, ISIN, LEI, exchange, transfer agent, auditor,
  newswire, read-by labels, source URLs). Show it as the record it is: fields, sources, who read what. That IS the pitch.
- Type: IBM Plex Sans, one family, all weights. (Its tailed lowercase l is why: "allooloo" must never read as I's.)
  Body max 72ch, left-aligned, sentence case. No all-caps eyebrows, no numbered 01/02/03 markers, no "§" section tags,
  no middle-dot meta strings, no arrows on links.
- Palette (5): paper #FFFFFF · ink #14213D · signed #0B6E4F (used only where a record is signed/sourced) ·
  grey #6B7280 · rule #E5E7EB. No dark mode in v1. No gradients, no cards-with-shadows, no per-section fade-ins.
- Motion: one moment only — the hero record "fills" its fields on first load, once. Reduced-motion respected.
- Mobile first; keyboard focus visible; contrast AA.

## IA (single page + three machine paths)
1 Masthead · 2 The record · 3 The desk · 4 The graph · 5 The orchestra · 6 Licence · 7 Proof · 8 Contact
Machine: /llms.txt · /facts.json · /.well-known/allooloo.json · plus sitemap.xml, robots.txt (agents allowed), JSON-LD Organization.

## Copy (paste as written; edit nothing for tone)

### 1 Masthead
Allooloo Technologies Corp.
Agentic Capital Markets Global Desk
2027, today.

### 2 The record
This is a Capital Markets Record.
[rendered CMR — real issuer, real sources, real read-by labels]
One signed record per listed company. Keyed on ISIN, ticker and LEI. Versioned, sourced, never deleted.
Every field names the registry it came from or the engine that read it. That is what an AI agent needs
before it can be trusted with a compliance duty — and what a terminal has never shown anyone.

### 3 The desk
Ask about any listed company in the markets you trade.
ask.allooloo.io is one door over twelve sovereign nodes. The identifier does the routing: a TSX name opens
the Canada node, a Xetra name opens the German node, in German if you asked in German. Default scope is the
market the name belongs to. Cross-border — dual listings, foreign parents, the holder who is in three of
your markets — is there when it's the question.
Built for the duty a dealer cannot decline: know every product on the shelf, continuously. KYP in Canada,
product governance in London and Frankfurt, reasonable-basis suitability in New York, DDO in Sydney,
product due diligence in Singapore. Same record, twelve names.

### 4 The graph
The Capital Markets Knowledge Graph.
Issuers as nodes. Insiders across boards, holders across names, auditors and transfer agents shared,
parents and subsidiaries, dual listings across markets, the newswire each issuer actually uses.
Served live to AI agents over MCP.
Twelve nodes, each a public registry and a door:
Canada · United Kingdom · Australia · Singapore · Switzerland · Germany · France · Netherlands ·
Hong Kong · Japan · South Korea · United States
Public-record only: SEDAR+, SEDI, Companies House, RNS, ASX, SGX, SIX, Xetra, EDGAR and their peers.
No prices. No quotes. No licensed market data. Nothing on the wire a data licence could pull back.

### 5 The orchestra
Eight engines. Named duties. Human cut.
Claude reads and adjudicates. ChatGPT extracts at scale. Gemini reads whole filings. Perplexity grounds
the cold read. Grok carries the live signal. Mistral reads the European nodes in their own languages.
Tavily is the net. Cloudflare is the network.
No engine is trusted alone. Every field carries who read it. A person cuts the record before it is signed.

### 6 Licence
Four things a dealer, bank or broker can sign. No services. Ever.
Dealer MCP access — your agents call the record directly, firm-wide.
Issuer record — your company's record, signed and live to every dealer agent.
Knowledge Graph API — the graph, for the agents you are already building.
Node operator — run a market under the standard, in your jurisdiction, under your regulator.
You license. You operate. We do not consult, integrate, or run your motion.

### 7 Proof
Live in production.
4,820 Canadian listed securities sourced and labelled in one session (Sept 10 2026) — 2,851 corporate
issuers across TSX, TSXV, CSE and Cboe Canada, every enriched cell carrying a source and a reader.
1T+ datapoints resolved into cited knowledge graphs. 50,000+ organizations spanned. Three regions.
Eight engines orchestrated, gated, adjudicated.
Custom graphs on Microsoft Azure. Google Cloud AI stack deployed as it ships. MCP end to end.
You can't hire your way into agentic operations. Allooloo is already running. Fleet, not headcount.

### 8 Contact
Tell us what you trade.
[form: name, firm, markets, message] — We reply within one business day.
Allooloo Technologies Corp. · Vancouver, Canada

## Machine surface (build these; they are the site for the second reader)
- /llms.txt — plain-text: who Allooloo is, what the CMR is, the twelve nodes, the licence shapes, the
  public-record rule, contact. Under 2,000 words. Keywords carried naturally: capital markets knowledge
  graph, MCP server, AI agents finance, agentic capital markets, issuer record, KYP, product governance,
  continuous disclosure, ISIN, LEI, SEDAR+, listed companies, investment dealer compliance, Model Context Protocol.
- /facts.json — the company as a record: legal name, jurisdiction, city, domains (all 51 from
  COMPANY RECORDS\Allooloo_Build_Domains_2026-09-10.xlsx), products (CM-KG, CMR, AI ASK), nodes (12),
  engines (8), licence shapes (4), dated "as_of". No signature field until cm-record signing exists — omit, don't stub.
- /.well-known/allooloo.json — same facts, well-known path.
- JSON-LD Organization in <head>: name, url, logo, sameAs (LinkedIn company page, X @ACM68000, github.com/allooloo).
- robots.txt: allow all, incl. GPTBot, ClaudeBot, PerplexityBot, Google-Extended, Bingbot. sitemap.xml listing / and the three machine paths.
- Do NOT publish mcp.* or ask.* hostnames as live links anywhere until those doors answer. Name them in prose only.

## Deploy
- Cloudflare Pages (or a single Worker serving static + the form handler) on the Allooloo Cloudflare account.
  FIRST: confirm the allooloo.io zone is in the account that AGENT KEYS\cloudflare.txt authenticates. If it is not,
  STOP and report — do not create the zone elsewhere.
- Custom domain allooloo.io, www 301 → apex. Edge cache on, HTML cached with short TTL, machine paths cached.
- Contact form: Worker → email to the CEO contact of record. No third-party form service.
- No forward from allooloo.ai in this order. That flip is a separate CEO go.

## Report
URL live · Lighthouse mobile score · the three machine paths fetched and shown · the rendered hero record
(which issuer) · what is broken. Nothing else.
