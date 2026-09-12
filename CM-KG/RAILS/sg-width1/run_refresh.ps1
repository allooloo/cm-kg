# Singapore Width 1 weekly refresh (ORDER-014 Part A, 2026-09-11). Pond rule: new drop, workers over a 7-day window, assembler merges every drop.
$ErrorActionPreference = 'Continue'
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\sg-cm-kg\.lock') { 'sg-cm-kg locked (build order in flight): refresh skipped'; exit 0 }
Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
python ..\pond_open.py sg-cm-kg sg-width1 width1
if (-not $env:WINDOW_DAYS) { $env:WINDOW_DAYS = '7' }
$env:THREADS = '4'
python sgxnet_search.py
python acra_events.py
python wire_search.py
python assemble_disclosure.py
