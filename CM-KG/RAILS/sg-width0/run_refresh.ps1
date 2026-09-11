# Singapore Width 0 refresh (monthly cadence once Width 1 exists; ORDER-013 Part B, 2026-09-11). Pond rule: opens a new width0 drop, re-runs every
# step into it, assembles from every drop (newest wins per key) and writes the versioned workbook to POND\sg-cm-kg\assembled\<date>\ + CM-KG\ISSUERS.
$ErrorActionPreference = 'Continue'
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\sg-cm-kg\.lock') { "sg-width0 refresh skipped: node lock present" | Out-File -Append 'C:\ALLOOLOO\CM-KG\RAILS\logs\sg-skipped.log'; exit 0 }
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
python ..\pond_open.py sg-cm-kg sg-width0 width0
python fetch_sources.py
python acra_index.py
python build_roster.py
python isin_lei_lookup.py
python lei_match.py
python lei_records.py
$env:THREADS = '3'
python enrich.py reg
python enrich.py wire
python assemble.py
