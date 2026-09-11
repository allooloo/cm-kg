# Canada passes 2 + 3 daily refresh — runs after CM-KG\RAILS\ca-width1\run_refresh.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
if (-not $env:LIVE_HOURS) { $env:LIVE_HOURS = '168' }   # weekly cadence (standing change 2026-09-10); daily not switched on
$env:LIVE_MAX_ISSUERS = '300'
python grok_live.py                       # 48-hour live layer (halts/resumes, silent issuers) -> raw/grok_live.jsonl, merged by the Width 1 assembler on the standing key
Copy-Item raw\grok_live.jsonl ..\ca-width1\raw\grok_live.jsonl -Force
python ..\ca-width1\assemble_disclosure.py
$env:THREADS = '6'; python fetch_bodies.py fast
$env:NF_DELAY = '3'; python fetch_bodies.py newsfile
python chatgpt_batch.py submit
$env:THREADS = '6'; python gemini_agm.py
$env:THREADS = '4'; python mistral_fr.py
$env:THREADS = '5'; python alias_sources.py
$env:THREADS = '4'; python perplexity_pages.py
$env:THREADS = '6'; $env:TARGETS = 'zero'; python website_alias.py   # alias channel 4: issuer website <title> for the zero-event issuers (standing change 2026-09-10)
$env:THREADS = '8'; python rematch.py
$env:THREADS = '8'; python confirm.py
# the batch usually completes within the hour; collect when it does, then rebuild
$deadline = (Get-Date).AddHours(6)
do { Start-Sleep -Seconds 300; $out = python chatgpt_batch.py collect } while ($out -notmatch 'collected' -and (Get-Date) -lt $deadline)
python rebuild_issuers.py
python rebuild_disclosure.py
Write-Output 'FILL+CONFIRM REFRESH DONE'
