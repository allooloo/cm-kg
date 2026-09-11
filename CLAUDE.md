# CLAUDE.md — C:\ALLOOLOO

You are Claude Code working for Allooloo Technologies Corp. This root is Allooloo only.

## Boot
1. Read START_ME_UP\MISSION.md and START_ME_UP\SWEEPS.md first, every session.
2. Run `gh auth switch --user allooloo` before any gh or git call. Sessions for any other root switch back.
3. Work in the product folder the order names. Never create a shared src.
4. Keys: AGENT KEYS\<lab>.txt — read at launch into an env var in-process. Never print, log, echo, or commit a key value.

## Hard rules
- This root is one company. Do not read from, import from, fork from, or reference C:\GREENCORE or any of its repos, canon, or nouns. Retail, CPG, BPC, GTIN, maker, retailer, banner: not in this codebase.
- Fly by wire: no test rigs, check scripts, or measurement harnesses before a roll. Roll, read the wire, report what is broken.
- Broken means broken. Never "built but not deployed" or "coming soon."
- Sourced or blank. No guessed aliases, no fuzzy matches, no inferred fields. Every enriched field carries source, read-by, and State (sourced · filled · confirmed · conflict).
- Country codes are written out (ca-cm-kg, de-cm-kg). Never a placeholder token for a country code.
- Money: plain "$" only. No currency codes, no conversions.
- Never name a Big Four accounting firm. Write "prepared for independent review."
- No time-of-day in reports. Date the work.
- Machine surfaces (mcp.*, resolvers, record endpoints) never sit behind a forward. Brand surfaces 301 to canonical. Never publish a door that isn't answering.
- Every Allooloo-related site's contact form posts to https://formspree.io/f/xbgjwaen with a hidden field name="site" set to that site's hostname.
- Buy, launch, and spend decisions are the CEO's. Report cost; never gate.
- Every order report ends with a spend line: credits, tokens and $ per engine for that order, plus the remaining Tavily and Anthropic balances read from their APIs. Report only; never gate.

## The pond (standing, all nodes — set Sept 11 2026)
1. Every harvest writes a dated, immutable drop under CM-KG\POND\<node>\<source>\<yyyy-mm-dd>\ — never overwrite, never delete; a re-run is a new drop (same day = suffix -2, -3).
2. Assemblers, Fill, Confirm and the door loader read only from the pond and write versioned outputs (CM-KG\POND\<node>\assembled\<date>\, mirrored to CM-KG\ISSUERS and CM-KG\DISCLOSURE). No worker reads a live source at assembly time.
3. The weekly sweep adds a drop and re-assembles by merging all drops, dedupe on the existing key.
4. One lock file per node while a build order is in flight (CM-KG\POND\<node>\.lock); the scheduled sweep skips if the lock exists. A build session takes the lock at the first harvest and releases it after the report.
Helper: CM-KG\RAILS\pond.py, one copy per rails folder (never a shared src). Why: on Sept 11 2026 the UK weekly task fired mid-build, deleted the Width 1 raw files and overwrote the 12-month event set with a 7-day run.

## Azure — Allooloo tenant only
- Tenant: Default Directory, domain allooloo.com, id 04a24e43-dc13-4578-950a-910db076a799
- Every session that touches Azure starts with:
    az login --tenant 04a24e43-dc13-4578-950a-910db076a799
    az account show
  and confirms the tenantId matches before any create, deploy, or delete.
- If az account show returns any other tenant, STOP and report. Never proceed on a default.
- Subscription name: to be confirmed by the CEO on first use; never assume one.

## GitHub — allooloo account only
- Repos: github.com/allooloo/cm-kg (this root's origin) · cm-record · hunter-agent · allooloo (profile README).
- Commit identity is repo-local (allooloo noreply). Scan every staged diff for key-shaped strings before commit.
- Token lacks `workflow` scope; nothing under .github/workflows/ until the CEO runs the refresh.

## Folders
- START_ME_UP\      boot: MISSION.md, SWEEPS.md, ORDER-00x files
- CM-KG\            graph, schema, node list; ISSUERS\ sweep workbooks; DISCLOSURE\ events; RAILS\ per-pass workers
- CM-RECORD\        CMR spec, signing, resolver
- SITE\             allooloo.io corporate build (Cloudflare Worker)
- AI-ASK\           the desk — ask.allooloo.io
- AGENT KEYS\       keys, one file per lab — never committed
- COMPANY RECORDS\  domains, registrations, invoices (advise only — never delete)
