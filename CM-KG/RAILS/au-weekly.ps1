# Allooloo CM-KG — Australia weekly sweep (SWEEPS.md cadence, pond rule): Width 1 refresh over a 7-day window, then passes 2 and 3, then the door reload and deploy.
# Task Scheduler "Allooloo CM-KG AU weekly": Friday 02:00 build-machine time (Central Standard Time (Mexico)) = Friday 18:00 AEST, after the ASX close.
# Skips while the node lock exists (a build order in flight). TMX Australia is not fetched (reCAPTCHA; HITL).
$ErrorActionPreference = 'Continue'
$root = 'C:\ALLOOLOO\CM-KG\RAILS'
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\au-cm-kg\.lock') { "AU weekly skipped: node lock present ($(Get-Content 'C:\ALLOOLOO\CM-KG\POND\au-cm-kg\.lock' -Raw))" | Out-File -Append (Join-Path $root 'logs\au-weekly-skipped.log'); exit 0 }
$log = Join-Path $root ('logs\au-weekly-' + (Get-Date -Format 'yyyy-MM-dd') + '.log'); New-Item -ItemType Directory -Force (Join-Path $root 'logs') | Out-Null
"== AU weekly start $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append
$env:WINDOW_DAYS = '7'
Set-Location (Join-Path $root 'au-width1'); & .\run_refresh.ps1 2>&1 | Tee-Object -FilePath $log -Append
Set-Location (Join-Path $root 'au-fill-confirm'); & .\run_refresh.ps1 2>&1 | Tee-Object -FilePath $log -Append
Set-Location (Join-Path $root 'door'); python load_nodes.py 2>&1 | Tee-Object -FilePath $log -Append
python load_d1.py 2>&1 | Tee-Object -FilePath $log -Append   # door store = D1 since 2026-09-11 (loads every node rendered under DOOR\data)
Set-Location 'C:\ALLOOLOO\CM-KG\DOOR'
$env:CLOUDFLARE_API_TOKEN = (Get-Content 'C:\ALLOOLOO\AGENT KEYS\cloudflare-d1.txt' -Raw).Trim(); $env:CLOUDFLARE_ACCOUNT_ID = 'dd2832b36f171b815f84c8487aada36b'
npx --yes wrangler deploy 2>&1 | Tee-Object -FilePath $log -Append
Remove-Item Env:CLOUDFLARE_API_TOKEN
"== AU weekly done $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append
