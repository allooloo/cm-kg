# Canada Width 1 daily refresh — last 48 hours, idempotent on (exchange, ticker, event type, date, URL).
# close-out 2026-10-10: a stderr line from a Python step is logged, never fatal (PowerShell 5.1 turns native stderr into a terminating
# error under 'Stop' and swallows the rest of the traceback). The step's own exit code decides: non-zero -> the rail exits with it.
$ErrorActionPreference = 'Continue'
function Py { python @args 2>&1 | ForEach-Object { "$_" }; if ($LASTEXITCODE -ne 0) { "STEP FAILED (exit $LASTEXITCODE): python $args"; exit $LASTEXITCODE } }
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
$env:WINDOW_DAYS = '7'   # ORDER-027 A2 (2026-10-17): seven days, the same window as the other ten nodes (was '2', a daily window on a weekly clock)
# pond rule: skip on the node lock; open a new dated drop (raw\ becomes a junction to it); nothing is deleted or moved
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\ca-cm-kg\.lock') { 'ca-cm-kg locked (build order in flight): refresh skipped'; exit 0 }
Py ..\pond_open.py ca-cm-kg ca-width1 width1
$env:SKIP_WIRE = 'Newsfile'   # Newsfile is read through newsfile_snippets.py (bot protection blocks direct fetch)
$env:THREADS = '5'; $a = Start-Process python -ArgumentList 'wire_pages.py'     -NoNewWindow -PassThru -RedirectStandardOutput 'raw\wire_pages.log'     -RedirectStandardError 'raw\wire_pages.err'
$env:THREADS = '6'; $b = Start-Process python -ArgumentList 'wire_search.py'    -NoNewWindow -PassThru -RedirectStandardOutput 'raw\wire_search.log'    -RedirectStandardError 'raw\wire_search.err'
$env:THREADS = '4'; $c = Start-Process python -ArgumentList 'tsxv_bulletins.py' -NoNewWindow -PassThru -RedirectStandardOutput 'raw\tsxv_bulletins.log' -RedirectStandardError 'raw\tsxv_bulletins.err'
Py cse_bulletins.py
$a.WaitForExit(); $b.WaitForExit(); $c.WaitForExit()
$env:THREADS = '12'; Py newsfile_snippets.py
$env:THREADS = '6';  $env:SKIP_DOMAINS = 'newsfilecorp.com,globenewswire.com'; Py release_dates.py
Py assemble_disclosure.py 'C:\ALLOOLOO\CM-KG\DISCLOSURE\ca-disclosure.xlsx' 'C:\ALLOOLOO\CM-KG\DISCLOSURE\events\ca-events.jsonl'
Write-Output 'REFRESH DONE'
# passes 2 and 3 (Fill + Confirm) — Grok live layer, lab reads, second-source confirmation, rebuilds
# ORDER-027 A4 (2026-10-17): WINDOW_DAYS is the HARVEST window; Fill + Confirm (rebuild_disclosure's Gemini AGM findings, rematch) must read the
# twelve-month disclosure window. The 2026-10-16 sweep carried the harvest window into the rebuild and dropped 65 in-window agm_record_date events.
Remove-Item Env:WINDOW_DAYS -ErrorAction SilentlyContinue   # common.py default: 365 days
& "$PSScriptRoot\..\ca-fill-confirm\run_refresh.ps1"
