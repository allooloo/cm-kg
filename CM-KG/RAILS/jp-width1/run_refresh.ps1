# jp Width 1 weekly refresh (ORDER-017 re-cut, 2026-09-12). Pond rule: new drop, workers over a 7-day window, assembler merges every drop. Global BUILD lock and node lock respected by pond_open.
$ErrorActionPreference = 'Continue'
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\.build-lock') { 'global BUILD lock present: refresh skipped'; exit 0 }
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\jp-cm-kg\.lock') { 'jp-cm-kg locked (build order in flight): refresh skipped'; exit 0 }
Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
python ..\pond_open.py jp-cm-kg jp-width1 width1
if (-not $env:WINDOW_DAYS) { $env:WINDOW_DAYS = '7' }
$env:THREADS = '3'
python edinet_events.py
python assemble_disclosure.py
