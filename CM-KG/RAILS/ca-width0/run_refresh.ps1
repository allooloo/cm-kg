# Canada Width 0 daily refresh — run from this folder. Keys are read from C:\ALLOOLOO\AGENT KEYS\ by keys.py at import; never echoed.
# Runtime on 2026-09-10 hardware: fetch ~2 min · CSE pages ~3 min · Tavily workers ~50 min in parallel · GLEIF name matcher ~80 min (60 req/min cap) · assemble ~1 min.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
$py = 'python'

& $py fetch_sources.py
& $py build_roster.py

# Deterministic exchange-site layer (CSE company pages) and the GLEIF name matcher run in the background
$cse  = Start-Process -FilePath $py -ArgumentList 'enrich.py','cse'  -NoNewWindow -PassThru -RedirectStandardOutput 'raw\enr_cse.log'  -RedirectStandardError 'raw\enr_cse.err'
$lei  = Start-Process -FilePath $py -ArgumentList 'lei_match.py'     -NoNewWindow -PassThru -RedirectStandardOutput 'raw\lei_match.log' -RedirectStandardError 'raw\lei_match.err'
$lei2 = Start-Process -FilePath $py -ArgumentList 'lei_match.py','--reverse' -NoNewWindow -PassThru -RedirectStandardOutput 'raw\lei_match2.log' -RedirectStandardError 'raw\lei_match2.err'

# Tavily workers (thread counts tuned to the Startup plan rate limit)
$env:THREADS = '8'; $isin  = Start-Process -FilePath $py -ArgumentList 'enrich.py','isin'  -NoNewWindow -PassThru -RedirectStandardOutput 'raw\enr_isin.log'  -RedirectStandardError 'raw\enr_isin.err'
$env:THREADS = '5'; $corp  = Start-Process -FilePath $py -ArgumentList 'enrich.py','corp'  -NoNewWindow -PassThru -RedirectStandardOutput 'raw\enr_corp.log'  -RedirectStandardError 'raw\enr_corp.err'
$env:THREADS = '6'; $wire  = Start-Process -FilePath $py -ArgumentList 'enrich.py','wire'  -NoNewWindow -PassThru -RedirectStandardOutput 'raw\enr_wire.log'  -RedirectStandardError 'raw\enr_wire.err'
$env:THREADS = '3'; $sedar = Start-Process -FilePath $py -ArgumentList 'enrich.py','sedar' -NoNewWindow -PassThru -RedirectStandardOutput 'raw\enr_sedar.log' -RedirectStandardError 'raw\enr_sedar.err'

$cse.WaitForExit(); $isin.WaitForExit(); $corp.WaitForExit(); $wire.WaitForExit(); $sedar.WaitForExit()
& $py enrich.py corp_cse_missing      # Tavily auditor/transfer-agent read only for CSE issuers whose page carries no auditor
$lei.WaitForExit(); $lei2.WaitForExit()

& $py isin_lei_lookup.py              # ISIN -> LEI from the GLEIF mapping file (exact)
& $py lei_records.py                  # jurisdiction / HQ / status for every LEI in play
& $py assemble.py 'C:\ALLOOLOO\CM-KG\ISSUERS\ca-issuers.xlsx'
Write-Output 'REFRESH DONE'
