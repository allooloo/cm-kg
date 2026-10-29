# mx Width 1 nightly refresh (NODE-ROW, DAY ORDER 5, 2026-10-24). The NODE-EU rail: RAILS\eu-node\eu_node.py reads the roster and the store
# (readers in RAILS\row-sources\mx) over the night's window, writes dated pond drops, and assembles the merged event set (never shorter).
$ErrorActionPreference = 'Continue'
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\.build-lock') { 'global BUILD lock present: refresh skipped'; exit 0 }
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\mx-cm-kg\.lock') { 'mx-cm-kg locked (build order in flight): refresh skipped'; exit 0 }
Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
if (-not $env:WINDOW_DAYS) { $env:WINDOW_DAYS = '3' }
python ..\eu-node\eu_node.py mx --days $env:WINDOW_DAYS
exit $LASTEXITCODE
