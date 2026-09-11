# CM-KG rail — United Kingdom Width 0 (uk-cm-kg) full re-harvest. Run from this folder. Keys load in-process from C:\ALLOOLOO\AGENT KEYS via keys.py.
# Aquis is not fetched here: aquis.eu refuses plain HTTP clients (HTTP 429). raw\aquis.json is refreshed by a browser session (see README) before this runs.
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
$log = Join-Path $PSScriptRoot ('raw\refresh-' + (Get-Date -Format 'yyyy-MM-dd') + '.log')
function Step($name, $cmd) { "== $name $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append; & $cmd 2>&1 | Tee-Object -FilePath $log -Append }
Remove-Item raw\lse_alldata.jsonl, raw\lse_issuer.jsonl, raw\lei_match.jsonl, raw\lei_records.jsonl, raw\ch_match.jsonl, raw\enr_reg.jsonl, raw\enr_wire.jsonl -ErrorAction SilentlyContinue
Step 'fetch (LSE explorer + sector sweep; GLEIF mapping; Companies House bulk if absent)' { python fetch_sources.py }
Step 'Companies House index' { python ch_index.py }
Step 'LSE instrument records (one thread; the API blocks bursts with HTTP 403)' { $env:THREADS = '1'; python lse_instruments.py }
Step 'LSE issuer profiles' { $env:THREADS = '1'; python lse_issuer_profile.py }
Step 'roster' { python build_roster.py }
Step 'GLEIF ISIN-to-LEI' { python isin_lei_lookup.py }
Step 'GLEIF name-exact fallback' { python lei_match.py }
Step 'GLEIF LEI records' { python lei_records.py }
Step 'Companies House match' { python ch_match.py }
Step 'Tavily registrar + auditor' { $env:THREADS = '3'; python enrich.py reg }
Step 'Tavily newswire' { $env:THREADS = '3'; python enrich.py wire }
Step 'assemble' { python assemble.py 'C:\ALLOOLOO\CM-KG\ISSUERS\uk-issuers.xlsx' }
"DONE $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append
