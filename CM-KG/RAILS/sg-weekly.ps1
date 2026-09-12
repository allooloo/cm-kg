# Allooloo CM-KG — Singapore weekly sweep (SWEEPS.md cadence, pond rule): Width 1 refresh over a 7-day window, then passes 2 and 3, then the door reload and deploy.
# Task Scheduler "Allooloo CM-KG SG weekly": Friday 03:30 build-machine time (Central Standard Time (Mexico)) = Friday 17:30 Singapore time, after the SGX close.
# Skips while the node lock exists (a build order in flight).
$ErrorActionPreference = 'Continue'
# global BUILD lock (SWEEPS.md, 2026-09-11): no scheduled sweep runs on any node while any build order is in flight
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\.build-lock') { "skipped: global BUILD lock present (a build order is in flight)" | Out-File -Append 'C:\ALLOOLOO\CM-KG\RAILS\logs\sweeps-skipped.log'; exit 0 }
$root = 'C:\ALLOOLOO\CM-KG\RAILS'
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\sg-cm-kg\.lock') { "SG weekly skipped: node lock present ($(Get-Content 'C:\ALLOOLOO\CM-KG\POND\sg-cm-kg\.lock' -Raw))" | Out-File -Append (Join-Path $root 'logs\sg-weekly-skipped.log'); exit 0 }
$log = Join-Path $root ('logs\sg-weekly-' + (Get-Date -Format 'yyyy-MM-dd') + '.log'); New-Item -ItemType Directory -Force (Join-Path $root 'logs') | Out-Null
"== SG weekly start $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append
$env:WINDOW_DAYS = '7'
Set-Location (Join-Path $root 'sg-width1'); & .\run_refresh.ps1 2>&1 | Tee-Object -FilePath $log -Append
Set-Location (Join-Path $root 'sg-fill-confirm'); & .\run_refresh.ps1 2>&1 | Tee-Object -FilePath $log -Append
Set-Location (Join-Path $root 'door'); python load_nodes.py 2>&1 | Tee-Object -FilePath $log -Append
python load_d1.py 2>&1 | Tee-Object -FilePath $log -Append   # door store = D1 since 2026-09-11 (loads every node rendered under DOOR\data)
Set-Location 'C:\ALLOOLOO\CM-KG\DOOR'
$env:CLOUDFLARE_API_TOKEN = (Get-Content 'C:\ALLOOLOO\AGENT KEYS\cloudflare-d1.txt' -Raw).Trim(); $env:CLOUDFLARE_ACCOUNT_ID = 'dd2832b36f171b815f84c8487aada36b'
npx --yes wrangler deploy 2>&1 | Tee-Object -FilePath $log -Append
Remove-Item Env:CLOUDFLARE_API_TOKEN
"== SG weekly done $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append
