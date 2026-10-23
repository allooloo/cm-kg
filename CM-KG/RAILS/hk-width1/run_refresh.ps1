# Hong Kong Width 1 refresh (ORDER-035, 2026-10-22). Pond rule: new drop, the HKEXnews worker over the window, the assembler merges every drop.
# The nightly sweep (ORDER-036) calls this with WINDOW_DAYS from the job (default 7); the build ran WINDOW_DAYS=366 once.
$ErrorActionPreference = 'Continue'
if ((Test-Path 'C:\ALLOOLOO\CM-KG\POND\hk-cm-kg\.lock') -and ($env:POND_IGNORE_LOCK -ne '1')) { 'hk-cm-kg locked (build order in flight): refresh skipped'; exit 0 }
Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
python ..\pond_open.py hk-cm-kg hk-width1 width1
if (-not $env:WINDOW_DAYS) { $env:WINDOW_DAYS = '7' }
$env:THREADS = '4'
python hkexnews_search.py
if ($LASTEXITCODE -ne 0) { "hkexnews worker exit $LASTEXITCODE"; exit $LASTEXITCODE }
python assemble_disclosure.py
exit $LASTEXITCODE
