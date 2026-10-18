# allooloo.io — build notes (ORDER-002, 2026-09-10)

One source, one deploy: a single Cloudflare Worker (`worker/index.js`) serving `public/` as static assets, redirecting www to the apex, and handling `POST /contact`.

## Build
```
python build_facts.py   # facts.json, .well-known/allooloo.json (51 domains from COMPANY RECORDS), hero.json (fullest corporate row of CM-KG\ISSUERS\ca-issuers.xlsx)
python build_site.py    # renders public/index.html from template.html + hero.json
npx wrangler deploy     # CLOUDFLARE_API_TOKEN from AGENT KEYS\cloudflare.txt, CLOUDFLARE_ACCOUNT_ID dd2832b36f171b815f84c8487aada36b
```
Copy lives in `template.html` exactly as written in the order. The hero record is never hand-typed; re-run the two build scripts after each Canada refresh.

## Design decisions (per the order)
IBM Plex Sans self-hosted (variable upright 400–700 + italic 400, latin subset, from Google Fonts' files). Five colours only. Signed green appears only on sources and read-by labels. One motion: the record fills once per session on first load (`hero.js`, sessionStorage guard, reduced-motion respected). Body measure 72ch. No dark mode, no gradients, no shadows, no eyebrows, no numbering, no arrows.

## Contact form
Standing rule (2026-09-10): the form posts to `https://formspree.io/f/xbgjwaen` with a hidden `site=allooloo.io` field. CSP `form-action` admits formspree.io. The Worker no longer handles `/contact` (it redirects to `/#contact`).

## Machine surface
`/llms.txt`, `/facts.json`, `/.well-known/allooloo.json`, `/hero.json`, `/sitemap.xml`, `/robots.txt` (all agents allowed), JSON-LD Organization in the head. mcp.* and ask.* are named in prose only.

## Cache
`public/_headers`: HTML 5 min with stale-while-revalidate, machine paths 1 h, fonts 1 y immutable, CSS/JS 1 d. Security headers and a self-only CSP, plus the one Cloudflare Web Analytics beacon host the zone auto-injects (the token cannot switch that injection off).

## Deploy note
`wrangler deploy` uploads and activates the version, then errors at the zone Workers Routes step (the token lacks that zone scope). That error is cosmetic: the two custom domains were attached once at account level (`PUT /accounts/{id}/workers/domains`, 2026-09-10) and persist across deploys. Zone settings applied 2026-09-10: Always Use HTTPS on, minimum TLS 1.2.
