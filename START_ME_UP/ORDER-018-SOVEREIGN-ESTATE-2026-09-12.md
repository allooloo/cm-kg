# ORDER-018 — SOVEREIGN ESTATE (CEO GO, Sept 12 2026)
Recorded verbatim from the CEO's message (final text, re-sent the same day with the DESIGN and APEX sections; the first cut is kept at the foot of this file).

TENANT OF RECORD
  Directory      Default Directory (allooloo.com)
  Directory ID   04a24e43-dc13-4578-950a-910db076a799
  Subscription   Azure subscription 1
  Subscription   038b49c0-5a0c-46f7-bd34-41ee6d087b41
Never another tenant. The subscription was cleared by the CEO on Sept 12; anything still showing "Deleting" is out of scope — create your own resource groups with your own names.

STEP 0 (done or in flight): read-only inventory — resource groups and state, Container Apps + Storage quotas in each target region. First line of the report.

RULINGS FROM 017 (act first, no report needed)
- Registry v0.10.0: PUBLISH. Ten nodes on the card.
- Euronext foreign-ISIN lines stay on the French door, type marked.
- Sweeps stay DISABLED, BUILD lock stays set, through this order.
- Review-tab disputes (JP registrar 11, KR registrar 362) stand as listed; no promotion, no re-run.

DESIGN
Control plane global, data plane regional. Each node's records and events live and are served in that node's Azure region. The apex on Cloudflare holds only the index (who lives where) and forwards; no record body ever sits outside its jurisdiction.

SCOPE — ALL ELEVEN LIVE, ONE RUN, NO STAGING
One image, region as a parameter, eleven regions:
  East US · Canada Central · UK South · France Central · West Europe · Switzerland North · Germany West Central · Australia East · Southeast Asia · Japan East · Korea Central
Hong Kong stays a Width 0 beacon; East Asia is a config line, not a deploy.

PER REGION
1. Storage account = the node's pond: every existing drop copied in as immutable dated blobs, RECORDS / EVENTS / INDEX, versioning on. Local pond stays where it is.
2. Container App running the node's door — same five tools, same answers, reading its own regional store. Store shape inside the region is your call; no new managed database unless the door can't run without one.
3. A2A Agent Card at the same origin: node identity, jurisdiction, capabilities (the five tools), contact. Thin is fine; published is the point.
4. Hostnames — two per node, both on the existing <node>-cm-kg.ai Cloudflare zone, both bound on the Container App as custom domains with a certificate (managed or Cloudflare Origin CA, your call), Cloudflare proxied, SSL full (strict):
     mcp.<node>-cm-kg.ai     → the door
     agent.<node>-cm-kg.ai   → the A2A Agent Card
   Cloudflare keeps DNS, proxy and edge; Azure must also know the name or the origin won't answer for it. Bind before flipping orange if the managed cert needs it. The existing mcp.* Worker route stays in place until the origin answers on the new binding, then the record flips. The Worker + D1 door is LEFT STANDING beside it.

APEX — mcp.capitalmarketsknowledgegraph.ai
Stays on Cloudflare as the router. After the eleven regional doors answer, re-cut the apex Worker to: index only (name / ticker / ISIN / LEI → node), list_nodes, and forwarding of record and event calls to the owning node's regional door. No record bodies stored at the apex. No fallback: if a node's regional door doesn't answer, the apex returns unavailable for that node — never a record from another store. Once the apex flips, nothing routes to the old shared D1; it stays standing (Rule One) and is listed for CEO deletion at end of scope. Agent Card at agent.capitalmarketsknowledgegraph.ai describes the router role and lists the eleven node agents.

UNITED STATES — INSIDE THIS ORDER
East US is also the US rail. Run the EDGAR pull from the container with a declared User-Agent (Allooloo Technologies Corp. + contact mailbox of record). Build US Width 0 → Width 1 → Fill → door on the standard pattern. Retire the 30-minute laptop retry once the container pull succeeds (disabled and logged, not deleted).

ORDER OF REGIONS
East US → Canada Central → UK South → the other eight straight through. The US container goes up first; the US data build runs in the background while the rest deploy. Apex re-cut last.

CLOSE
Registry server.json staged at v0.11.0, eleven doors and twelve Agent Cards (eleven nodes + apex). Not published — CEO go.

STANDING
Fly-by-wire: shape calls are yours (image, runtime, store, concurrency, naming), logged in START_ME_UP\ORDER-018-BUILD-LOG. No pausing, no check-ins on shape. Rule One: nothing of ours deleted or overwritten, anywhere, Azure included. Broken is broken.

HITL — LIST, THEN CONTINUE ON WHAT DOESN'T NEED IT
- Contact mailbox for the EDGAR User-Agent if none is on record.
- Anthropic admin key (standing).

REPORT
One report at the end: Step 0 inventory; eleven regions with door URL and Agent Card URL; apex re-cut state; pond blob counts per node; US counts (records, events, Fill); registry version staged; HITL list; spend line — Azure separate from lab.

---
## First cut (received minutes earlier, same day; superseded by the text above)
Identical except: no DESIGN section; PER REGION item 4 read "Cloudflare stays in front — mcp.<node>-cm-kg.ai origin flipped to the Container App, proxied, edge cache as today. The existing Worker + D1 door is LEFT STANDING beside it."; no APEX section; CLOSE read "eleven doors and eleven Agent Cards"; ORDER OF REGIONS had no "Apex re-cut last"; REPORT had no "apex re-cut state".
