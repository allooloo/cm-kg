# CM-KG rail — Australia Width 0 (au-cm-kg) full re-harvest. Run from this folder. Keys load in-process from C:\ALLOOLOO\AGENT KEYS via keys.py.
# Pond rule: a new drop is opened first (raw\ becomes a junction to POND\au-cm-kg\width0\<date>\); the previous drop is closed and immutable; the assembler
# reads every drop (newest wins per key) and writes a versioned workbook under POND\au-cm-kg\assembled\<date>\, mirrored to CM-KG\ISSUERS\au-issuers.xlsx.
# Skips when the node lock exists (a build order in flight). TMX Australia rows need a browser-session read into raw\tmxau.json (HITL).
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\au-cm-kg\.lock') { 'au-cm-kg locked (build order in flight): refresh skipped'; exit 0 }
python ..\pond_open.py au-cm-kg au-width0 width0
$log = Join-Path $PSScriptRoot ('refresh-' + (Get-Date -Format 'yyyy-MM-dd') + '.log')
function Step($name, $cmd) { "== $name $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append; & $cmd 2>&1 | Tee-Object -FilePath $log -Append }
Step 'fetch (ASX directory + company records, NSX feed, ASIC dataset, GLEIF mapping)' { $env:THREADS = '4'; python fetch_sources.py }
Step 'ASIC index' { python asic_index.py }
Step 'ASX announcements (12 months)' { $env:THREADS = '4'; python asx_announcements.py }
Step 'roster' { python build_roster.py }
Step 'GLEIF ISIN-to-LEI' { python isin_lei_lookup.py }
Step 'GLEIF name-exact fallback' { python lei_match.py }
Step 'GLEIF LEI records' { python lei_records.py }
Step 'Tavily share registry' { $env:THREADS = '4'; python enrich.py reg }
Step 'Tavily newswire' { $env:THREADS = '4'; python enrich.py wire }
Step 'assemble' { python assemble.py 'C:\ALLOOLOO\CM-KG\ISSUERS\au-issuers.xlsx' }
"DONE $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append
