# Canada passes 2 + 3 daily refresh — runs after CM-KG\RAILS\ca-width1\run_refresh.ps1
# close-out 2026-10-10: a stderr line from a Python step is logged, never fatal (PowerShell 5.1 turns native stderr into a terminating
# error under 'Stop' and swallows the rest of the traceback). The step's own exit code decides: non-zero -> the rail exits with it.
$ErrorActionPreference = 'Continue'
function Py { python @args 2>&1 | ForEach-Object { "$_" }; if ($LASTEXITCODE -ne 0) { "STEP FAILED (exit $LASTEXITCODE): python $args"; exit $LASTEXITCODE } }
Set-Location $PSScriptRoot
# pond rule: skip on the node lock; open a new dated drop (raw\ becomes a junction to it); nothing is deleted or moved
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\ca-cm-kg\.lock') { 'ca-cm-kg locked (build order in flight): refresh skipped'; exit 0 }
Py ..\pond_open.py ca-cm-kg ca-fill-confirm fill-confirm
$env:PYTHONIOENCODING = 'utf-8'
if (-not $env:LIVE_HOURS) { $env:LIVE_HOURS = '168' }   # weekly cadence (standing change 2026-09-10); daily not switched on
$env:LIVE_MAX_ISSUERS = '300'
Py grok_live.py                       # 48-hour live layer (halts/resumes, silent issuers) -> raw/grok_live.jsonl, merged by the Width 1 assembler on the standing key
Copy-Item raw\grok_live.jsonl ..\ca-width1\raw\grok_live.jsonl -Force
Py ..\ca-width1\assemble_disclosure.py
$env:THREADS = '6'; Py fetch_bodies.py fast
$env:NF_DELAY = '3'; Py fetch_bodies.py newsfile
Py chatgpt_batch.py submit
$env:THREADS = '6'; Py gemini_agm.py
$env:THREADS = '4'; Py mistral_fr.py
$env:THREADS = '5'; Py alias_sources.py
$env:THREADS = '4'; Py perplexity_pages.py
$env:THREADS = '6'; $env:TARGETS = 'zero'; Py website_alias.py   # alias channel 4: issuer website <title> for the zero-event issuers (standing change 2026-09-10)
$env:THREADS = '8'; Py rematch.py
$env:THREADS = '8'; Py confirm.py
# the batch usually completes within the hour; collect when it does, then rebuild
$deadline = (Get-Date).AddHours(6)
# ORDER-026 (2026-10-17): $out is an array of lines; '-notmatch' on an array filters it, so the 'status' line kept the loop alive to the 6-hour deadline
# after the batch was collected (2026-10-16 sweep: batch done 03:03, loop ran on). Join the lines before the test.
do { Start-Sleep -Seconds 300; $out = (python chatgpt_batch.py collect) -join "`n" } while ($out -notmatch 'collected' -and (Get-Date) -lt $deadline)
Py rebuild_issuers.py
Py rebuild_disclosure.py
Write-Output 'FILL+CONFIRM REFRESH DONE'
