# CM-KG rail — Australia Width 1 (Disclosure) weekly refresh: the same workers over the last 7 days in a new pond drop, merged on (exchange, code, type, date, URL).
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\au-cm-kg\.lock') { 'au-cm-kg locked (build order in flight): refresh skipped'; exit 0 }
python ..\pond_open.py au-cm-kg au-width1 width1
$env:WINDOW_DAYS = if ($env:WINDOW_DAYS) { $env:WINDOW_DAYS } else { '7' }
$log = Join-Path $PSScriptRoot ('raw\refresh-' + (Get-Date -Format 'yyyy-MM-dd') + '.log')
function Step($name, $cmd) { "== $name $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append; & $cmd 2>&1 | Tee-Object -FilePath $log -Append }
Step 'ASX announcements' { $env:THREADS = '4'; python asx_events.py }
Step 'ASIC register events' { python asic_events.py }
Step 'NSX feed' { python nsx_events.py }
Step 'Newswire search' { $env:THREADS = '4'; python wire_search.py }
Step 'assemble' { python assemble_disclosure.py 'C:\ALLOOLOO\CM-KG\DISCLOSURE\au-disclosure.xlsx' 'C:\ALLOOLOO\CM-KG\DISCLOSURE\events\au-events.jsonl' }
"DONE $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append
