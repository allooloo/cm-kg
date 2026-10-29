# no Width 1 nightly refresh (NODE-EU, DAY ORDER 4, 2026-10-24). One rail for the European nodes: RAILS\eu-node\eu_node.py reads the roster (ESMA FIRDS)
# and the national regulated-information store over the night's window, writes dated pond drops, and assembles the merged event set (never shorter).
$ErrorActionPreference = 'Continue'
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\.build-lock') { 'global BUILD lock present: refresh skipped'; exit 0 }
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\no-cm-kg\.lock') { 'no-cm-kg locked (build order in flight): refresh skipped'; exit 0 }
Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
if (-not $env:WINDOW_DAYS) { $env:WINDOW_DAYS = '3' }
python ..\eu-node\eu_node.py no --days $env:WINDOW_DAYS
exit $LASTEXITCODE
