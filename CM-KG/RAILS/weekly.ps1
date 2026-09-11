# Allooloo CM-KG — Canada weekly run (standing cadence, 2026-09-10): live layer + Width 1 refresh + Fill + Confirm over a 7-day window.
# Scheduled: Friday 18:00 machine time (Central Standard Time (Mexico), no daylight shift) = 19:00 EST / 20:00 EDT America/Toronto, after TSX close.
$ErrorActionPreference = 'Continue'
$log = "C:\ALLOOLOO\CM-KG\RAILS\logs\weekly-$(Get-Date -Format yyyyMMdd-HHmm).log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
Start-Transcript -Path $log
$env:PYTHONIOENCODING = 'utf-8'
$env:WINDOW_DAYS = '7'; $env:LIVE_HOURS = '168'
# Width 1: last 7 days of releases and bulletins (workers resume-safe; assembler merges on the standing key)
Set-Location 'C:\ALLOOLOO\CM-KG\RAILS\ca-width1'
& '.\run_refresh.ps1'        # chains ca-fill-confirm\run_refresh.ps1 (Grok live layer, lab reads, website alias channel, rematch, confirm, rebuilds)
Stop-Transcript
