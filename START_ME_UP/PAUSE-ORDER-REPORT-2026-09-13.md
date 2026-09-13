# PAUSE ORDER — report (CEO go, Sept 13 2026)

## 1. Deletions — the four, listed and done
1. Cloudflare Worker `cm-kg-door` (the ORDER-010 door) — check: no custom domain bound, no route — **deleted**.
2. D1 database `cm-kg` (fad284a8-9f96-4a2f-afd5-f364302828bc, 478 MB) — check: its only binder was the Worker above, already gone — **deleted**.
3. Container Apps environment `cmkg-env-eastus` (Failed since ORDER-018) — check: provisioningState Failed, zero apps on it — **deleted**.
4. The four failed executions of job `cmkg-us-rail` (`innnyur`, `fd5vrmb`, `ulhdixz`, `3gyuke4`) — check: all Failed — **not deletable as objects**: the platform answers Method Not Allowed to a DELETE on an execution; they are history records that age out under the job's retention. Reported, not forced.

Nothing beyond the four. Record: `AZURE\deletions-2026-09-13.txt`.

## 2. Sweep rail — test result
- **Upload only the new drop:** `provision_region.py upload` now sends the newest dated drop per source (`assembled`, `fill-confirm`, `width0`, `width1` …), never the whole pond; earlier drops are already in the store and immutable. Facts are stamped `store_reloaded_at` (UTC) at every reload.
- **Door refreshes without a restart:** door image `cmkg-door:0.11.3` reloads index, facts and nodes together every ten minutes, each download independent of the others' failure; all eleven doors moved to it.
- **Test on the Netherlands node, no wire search:** load + upload in **87 s wall time** (newest drop per source, 0 new blobs — already in the store; door records, events and index re-sent). The door showed the new stamp on its own ten-minute cycle without a revision restart, twice: store_reloaded_at 13:21:25Z seen by the 13:29 refresh and 13:31:19Z by the 13:39 refresh (473 s after the second upload). The door's `booted` field is the time of its last store refresh (BOOTED is set on every cycle), which is why it moved at 13:29 and 13:39 — refreshes, not restarts; the field is renamed to `refreshed` in the next image.

## 3. Favicon — by fetch
The set of record from `C:\ALLOOLOO\SITE\` serves at the standard paths on all 22 surfaces with the `<link>` tags in the shared head. Byte-identical md5 to the SITE files on allooloo.io, kr-cm-kg.ai, agentic-esg.ai and kyp-model.ai for favicon.svg, favicon.ico, icon-192, icon-512 and apple-touch-icon; eight link tags on allooloo.io.

## 4. Agent readiness — before / after per surface class
`START_ME_UP_5` is not on disk under `C:\ALLOOLOO\START_ME_UP` (searched the whole Allooloo root); the kit stands as built on Sept 12 and kyp-model.ai is the reference. Scans via `POST /api/scan`:

| Surface class | Before | After | Pass · neutral · fail |
|---|---|---|---|
| allooloo.io (company) | Level 5 Agent-Native | Level 5 Agent-Native | 12 · 6 · 4 of 22 |
| uk-cm-kg.ai (node) | Level 5 Agent-Native | Level 5 Agent-Native | 12 · 6 · 4 of 22 |
| kyp-model.ai (reference) | Level 5 Agent-Native | Level 5 Agent-Native | 12 · 6 · 4 of 22 |

Identical check sets on all three; the API returns no numeric score (the site's 73 is its rendering of the same 22 checks). Per check: robotsTxt P · sitemap P · linkHeaders P · dnsAid F · markdownNegotiation P · robotsTxtAiRules P · contentSignals P · webBotAuth N · apiCatalog P · oauthDiscovery F · oauthProtectedResource P · authMd F · mcpServerCard P · a2aAgentCard P · agentSkills P · webMcp F · ard P · x402/mpp/ucp/acp/ap2 N.

**Every remaining fail, with its cause:**
- `dnsAid` — DNS for AI Discovery records (`_agents` SVCB/HTTPS/TXT) — DNS day; reported, not chased.
- `oauthDiscovery` — `/.well-known/openid-configuration` and `oauth-authorization-server` answer 404 on purpose: no authorization server exists, the doors are open by design.
- `authMd` — the check wants a non-empty `authorization_servers` array in the protected-resource metadata; none exists, stated truthfully in `auth.md`.
- `webMcp` — needs JavaScript on the page; the record-grade standard is zero scripts.
- Neutral: `webBotAuth` (informational) and the five commerce checks (not a commerce site).

## 5. Home footer — fixed
allooloo.io footer line now reads: `The agents that built this read their own mail: allooloo@hey.com · Allooloo Technologies Corp. · Vancouver & Toronto, Canada · CEO Letter` (no period before the separator).

Surfaces version 2026-09-13.1; snapshot `POND\estate\surfaces\2026-09-13-2`; build-log items 43–47.
