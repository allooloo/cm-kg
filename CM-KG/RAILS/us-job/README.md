# us-job — the United States rail as an Azure Container Apps job (ORDER-018)

Runs in East US (`allooloo-cmkg-eastus`, job `cmkg-us-rail`, image `allooloocmkg.azurecr.io/cmkg-us-job`), writes only to the East US store `allooloocmkguspond` (container `pond`).

- **Sources:** EDGAR `company_tickers_exchange.json` (roster, exchange), `data.sec.gov/submissions/CIK##########.json` (name as filed, SIC, state of incorporation, fiscal year end, filer category, EIN, addresses, former names, filings index), 10-K inline XBRL (`dei:AuditorName`, `dei:AuditorLocation`, period end); GLEIF golden copy staged in the pond (`estate/gleif-golden/<date>/lei-US.jsonl`, ISIN mapping zip); Gemini (transfer agent from the 10-K cover), Perplexity fast (issuer page and alias).
- **User-Agent of record:** `Allooloo Technologies Corp. developers@allooloo.ai` (env `CONTACT`; the same mailbox for any registration). EDGAR refuses a GitHub noreply address as the contact — 403 "undeclared automated tool" from every network; the mailbox of record answers 200. Under 8 requests a second, `Accept-Encoding: gzip`.
- **Writes:** `pond/width0/<date>/` (submissions, roster, job log) — immutable dated drops; `door/records/<EX>/<code>.json`, `door/events/<EX>/<code>.json`, `door/index.json`, `door/facts.json`, `door/nodes.json` (the US line marked live). The door container re-reads its index every ten minutes; the apex index is rebuilt with `CM-KG\DOOR\apex\build_index.py` then `wrangler deploy`.
- **Run:** `az containerapp job start -g allooloo-cmkg-eastus -n cmkg-us-rail`; logs `az containerapp job logs show … --container cmkg-us-rail`. Two-hour timeout, 1 vCPU / 2 GiB. Secrets: storage-key, gemini-key, pplx-key (set with `job update --set-env-vars` — `job create` mis-maps several `secretref:` values to one secret).
- **No schedule** while `CM-KG\POND\.build-lock` stands (see START_ME_UP\SWEEPS.md).
- **Never derived:** ISINs come only from the GLEIF mapping; blank stays blank. No prices.
