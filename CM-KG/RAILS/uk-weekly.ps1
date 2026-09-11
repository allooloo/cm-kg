# Allooloo CM-KG — United Kingdom weekly sweep (SWEEPS.md cadence): Width 1 refresh over a 7-day window, then passes 2 and 3, then the door reload.
# Task Scheduler "Allooloo CM-KG UK weekly": Friday 12:00 build-machine time (Central Standard Time (Mexico), no daylight shift) = 18:00 London in summer (19:00 in winter), after the LSE close.
# Aquis announcements are not fetched by machine (aquis.eu refuses plain clients): the browser-session read of the feed is a standing HITL item; the assembler keeps the last ingested rows.
$ErrorActionPreference = 'Continue'
$root = 'C:\ALLOOLOO\CM-KG\RAILS'
# pond rule 4: skip when a build order holds the node lock
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\uk-cm-kg\.lock') { "UK weekly skipped: node lock present ($(Get-Content 'C:\ALLOOLOO\CM-KG\POND\uk-cm-kg\.lock' -Raw))" | Out-File -Append (Join-Path $root 'logs\uk-weekly-skipped.log'); exit 0 }
$log = Join-Path $root ('logs\uk-weekly-' + (Get-Date -Format 'yyyy-MM-dd') + '.log'); New-Item -ItemType Directory -Force (Join-Path $root 'logs') | Out-Null
"== UK weekly start $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append
$env:WINDOW_DAYS = '7'
Set-Location (Join-Path $root 'uk-width1'); & .\run_refresh.ps1 2>&1 | Tee-Object -FilePath $log -Append
Set-Location (Join-Path $root 'uk-fill-confirm'); & .\run_refresh.ps1 2>&1 | Tee-Object -FilePath $log -Append
Set-Location (Join-Path $root 'door'); python load_nodes.py 2>&1 | Tee-Object -FilePath $log -Append
Set-Location 'C:\ALLOOLOO\CM-KG\DOOR'
$env:CLOUDFLARE_API_TOKEN = (Get-Content 'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt' -Raw).Trim(); $env:CLOUDFLARE_ACCOUNT_ID = 'dd2832b36f171b815f84c8487aada36b'
npx --yes wrangler deploy 2>&1 | Tee-Object -FilePath $log -Append
Remove-Item Env:CLOUDFLARE_API_TOKEN
"== UK weekly done $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append
