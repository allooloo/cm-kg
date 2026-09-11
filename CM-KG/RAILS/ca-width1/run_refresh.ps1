# Canada Width 1 daily refresh — last 48 hours, idempotent on (exchange, ticker, event type, date, URL).
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
$env:WINDOW_DAYS = '2'
# pond rule: skip on the node lock; open a new dated drop (raw\ becomes a junction to it); nothing is deleted or moved
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\ca-cm-kg\.lock') { 'ca-cm-kg locked (build order in flight): refresh skipped'; exit 0 }
python ..\pond_open.py ca-cm-kg ca-width1 width1
$env:SKIP_WIRE = 'Newsfile'   # Newsfile is read through newsfile_snippets.py (bot protection blocks direct fetch)
$env:THREADS = '5'; $a = Start-Process python -ArgumentList 'wire_pages.py'     -NoNewWindow -PassThru -RedirectStandardOutput 'raw\wire_pages.log'     -RedirectStandardError 'raw\wire_pages.err'
$env:THREADS = '6'; $b = Start-Process python -ArgumentList 'wire_search.py'    -NoNewWindow -PassThru -RedirectStandardOutput 'raw\wire_search.log'    -RedirectStandardError 'raw\wire_search.err'
$env:THREADS = '4'; $c = Start-Process python -ArgumentList 'tsxv_bulletins.py' -NoNewWindow -PassThru -RedirectStandardOutput 'raw\tsxv_bulletins.log' -RedirectStandardError 'raw\tsxv_bulletins.err'
python cse_bulletins.py
$a.WaitForExit(); $b.WaitForExit(); $c.WaitForExit()
$env:THREADS = '12'; python newsfile_snippets.py
$env:THREADS = '6';  $env:SKIP_DOMAINS = 'newsfilecorp.com,globenewswire.com'; python release_dates.py
python assemble_disclosure.py 'C:\ALLOOLOO\CM-KG\DISCLOSURE\ca-disclosure.xlsx' 'C:\ALLOOLOO\CM-KG\DISCLOSURE\events\ca-events.jsonl'
Write-Output 'REFRESH DONE'
# passes 2 and 3 (Fill + Confirm) — Grok live layer, lab reads, second-source confirmation, rebuilds
& "$PSScriptRoot\..\ca-fill-confirm\run_refresh.ps1"
