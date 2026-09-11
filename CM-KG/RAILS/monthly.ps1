# Allooloo CM-KG — Canada monthly full identity re-harvest (standing cadence, 2026-09-10): Width 0 from scratch, jurisdiction from GLEIF only,
# unclassified fund rows out of corporate scope, then the Fill + Confirm columns re-applied.
# Scheduled: 15th of the month 18:00 machine time = 19:00 EST / 20:00 EDT America/Toronto, after TSX close and after the TMX monthly listed-companies workbook is out.
$ErrorActionPreference = 'Continue'
# pond rule 4: skip when a build order holds the node lock
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\ca-cm-kg\.lock') { "Canada monthly skipped: node lock present" | Out-File -Append 'C:\ALLOOLOO\CM-KG\RAILS\logs\monthly-skipped.log'; exit 0 }
$log = "C:\ALLOOLOO\CM-KG\RAILS\logs\monthly-$(Get-Date -Format yyyyMMdd-HHmm).log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
Start-Transcript -Path $log
$env:PYTHONIOENCODING = 'utf-8'
Set-Location 'C:\ALLOOLOO\CM-KG\RAILS\ca-width0'
# clean sweep: every worker re-reads (the roster, ISIN, LEI, transfer agent, auditor, newswire, jurisdiction)
Remove-Item -Path 'raw\enr_*.jsonl','raw\lei_match*.jsonl','raw\lei_records.jsonl','raw\isin_lei_hits.json' -ErrorAction SilentlyContinue
& '.\run_refresh.ps1'
# re-apply passes 2 and 3 columns to the fresh identity workbook
Set-Location 'C:\ALLOOLOO\CM-KG\RAILS\ca-fill-confirm'
Remove-Item -Path 'raw\confirm_fields.jsonl','raw\aliases.jsonl' -ErrorAction SilentlyContinue
Remove-Item -Path 'C:\ALLOOLOO\CM-KG\ISSUERS\ca-issuers-width0.xlsx' -ErrorAction SilentlyContinue
$env:THREADS = '5'; python alias_sources.py
$env:THREADS = '8'; python confirm.py
python conflict_adjudicate.py
python rebuild_issuers.py
Stop-Transcript
