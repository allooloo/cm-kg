# au-width1 — Australia Width 1 (ORDER-011), disclosure events over 12 months

Pond-native rail for node `au-cm-kg`. Workers write into `raw\` (a directory junction to the open drop `CM-KG\POND\au-cm-kg\width1\<date>\`); the assembler reads every drop of the rail plus the last versioned event set, dedupes on (exchange, code, type, date, URL), and writes `CM-KG\DISCLOSURE\au-disclosure.xlsx` + `CM-KG\DISCLOSURE\events\au-events.jsonl` with a versioned copy under `CM-KG\POND\au-cm-kg\assembled\<date>\`.

## First run — 2026-09-11 (12-month window, 1,792 issuers from au-issuers.xlsx: ASX 1,748 corporates + funds, NSX 44)

| Worker | Source | Read-by label | Events |
|---|---|---|---|
| asx_events.py | asx.com.au announcements search (HTML, `by=asxCode`, per year, paged) | asx.com.au announcements search (exchange site) | 122,216 |
| wire_search.py (+ shards b, c) | Tavily on PR Newswire, GlobeNewswire, Business Wire, ACCESS Newswire, Newsfile, Medianet, PRWire | Tavily search (wire domains) + published_date / + URL date | 1,873 |
| asic_events.py | ASIC Company Dataset (data.gov.au, weekly): name changes, status changes | ASIC company register bulk dataset (data.gov.au, weekly) | 142 |
| nsx_events.py | nsx.com.au company news RSS | nsx.com.au company news feed (exchange feed) | 48 |

Assembled: **124,279 events**, every one dated and URL-carrying, State `sourced`. Price-sensitive (ASX marker): 29,856. Issuers with at least one event: 1,776 of 1,792 (zero events: 16 — 4 ASX non-primary lines and 12 NSX names).

By type: asx_announcement 53,342 · corporate_action 25,134 · substantial_holder 11,149 · director_interest 10,928 · agm_record_date 7,841 · financial_statement 6,683 · quarterly 5,163 · halt_resume 2,191 · newswire_release 1,691 · name_change 137 · nsx_announcement 15 · status_change 5.

Gaps: 67 rows — 47 `asic_events: no ACN / ASIC row in Width 0` (register events cannot be read without an ACN), 20 wire hits set aside under the name rule (ambiguous match). HITL tab: TMX Australia list, ASIC Connect API key, Anthropic Admin key.

### Build-day notes
- The ASX search cell carries `<n> pages <size>` after the headline; the worker now strips it (`asx_events.py`) and the assembler cleans earlier drops and the prior assembled set (`PAGES`). Assembled drop `2026-09-11-2` (uncleaned headlines) is superseded by `2026-09-11-3`.
- wire_search ran as three shards (`wire_search.py`, `wire_search_b.py` reverse order, `wire_search_c.py` from the middle) to finish inside the build day; `wire_merge_wait.py` merged them by key (first write wins; 86 issuers were read twice = 172 duplicate Tavily searches). The weekly refresh runs the single worker.
- The Tavily usage endpoint lags: it still reported the ORDER-010 Part B balance (40,897 of 100,000) after 3,756 wire searches this order.

## Refresh
`run_refresh.ps1` (called by `CM-KG\RAILS\au-weekly.ps1`, Friday 02:00 machine time = 18:00 AEST): `pond_open.py au-cm-kg au-width1 width1`, then the four workers with `WINDOW_DAYS=7`, then `assemble_disclosure.py`. Skips while `POND\au-cm-kg\.lock` exists.
