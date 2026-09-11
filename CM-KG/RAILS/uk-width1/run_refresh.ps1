# CM-KG rail — United Kingdom Width 1 (Disclosure) weekly refresh: the same workers over the last 7 days, merged on (exchange, ticker, type, date, URL).
# Aquis announcements are not fetched here (aquis.eu refuses plain clients): refresh raw/aquis_announcements.json in a browser session with aquis_ingest.py first.
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
$env:WINDOW_DAYS = if ($env:WINDOW_DAYS) { $env:WINDOW_DAYS } else { '7' }
$log = Join-Path $PSScriptRoot ('raw\refresh-' + (Get-Date -Format 'yyyy-MM-dd') + '.log')
function Step($name, $cmd) { "== $name $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append; & $cmd 2>&1 | Tee-Object -FilePath $log -Append }
# pond rule: skip on the node lock; open a new dated drop (raw\ becomes a junction to it); nothing is deleted or moved
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\uk-cm-kg\.lock') { 'uk-cm-kg locked (build order in flight): refresh skipped'; exit 0 }
python ..\pond_open.py uk-cm-kg uk-width1 width1
Step 'RNS via Investegate' { $env:THREADS = '4'; python investegate.py }
Step 'Companies House filings' { $env:THREADS = '3'; python ch_filings.py }
Step 'Newswire search' { $env:THREADS = '4'; python wire_search.py }
Step 'assemble' { python assemble_disclosure.py 'C:\ALLOOLOO\CM-KG\DISCLOSURE\uk-disclosure.xlsx' 'C:\ALLOOLOO\CM-KG\DISCLOSURE\events\uk-events.jsonl' }
"DONE $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append
