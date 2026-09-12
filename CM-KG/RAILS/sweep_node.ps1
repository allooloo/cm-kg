# CM-KG weekly sweep per node (ORDER-020 §10, re-armed Sept 12 2026):
#   harvest -> immutable pond drop -> regional store reload -> apex list_nodes updates -> surfaces re-render -> one line to NODE-SURFACES.md NUMBERS LOG.
# Usage: powershell -File sweep_node.ps1 <cc> <azure-region>      e.g. sweep_node.ps1 uk uksouth
# Skips on the global BUILD lock (CM-KG\POND\.build-lock) or the node lock (POND\<cc>-cm-kg\.lock). Nothing deleted; new drops beside old.
param([Parameter(Mandatory=$true)][string]$cc, [Parameter(Mandatory=$true)][string]$region)
$ErrorActionPreference = 'Continue'
$root = 'C:\ALLOOLOO'; $rails = "$root\CM-KG\RAILS"
$log = "$root\CM-KG\SWEEPS\$cc-$(Get-Date -Format 'yyyy-MM-dd').log"; New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
function Step($name, $cmd) { "== $name $(Get-Date -Format 'yyyy-MM-dd HH:mm')" | Tee-Object -FilePath $log -Append; & $cmd 2>&1 | Tee-Object -FilePath $log -Append }
if (Test-Path "$root\CM-KG\POND\.build-lock") { "global BUILD lock set: sweep skipped" | Tee-Object -FilePath $log -Append; exit 0 }
if (Test-Path "$root\CM-KG\POND\$cc-cm-kg\.lock") { "$cc-cm-kg locked: sweep skipped" | Tee-Object -FilePath $log -Append; exit 0 }
$env:PYTHONIOENCODING = 'utf-8'
if ($cc -eq 'us') {
  # the United States rail is the East US container job; one run, wait for it, then the estate steps
  Step 'us job start' { az containerapp job start -g allooloo-cmkg-eastus -n cmkg-us-rail -o none }
  Step 'us job wait' { $deadline = (Get-Date).AddHours(4); do { Start-Sleep -Seconds 120; $st = az containerapp job execution list -g allooloo-cmkg-eastus -n cmkg-us-rail --query "[0].properties.status" -o tsv } while ($st -eq 'Running' -and (Get-Date) -lt $deadline); "us job status: $st" }
} else {
  Step 'harvest (Width 1 refresh, 7-day window, new pond drop)' { Set-Location "$rails\$cc-width1"; & ".\run_refresh.ps1" }
  Step 'door data' { Set-Location "$rails\door"; python load_nodes.py $cc }
  Step 'regional store reload' { Set-Location "$root\AZURE"; python provision_region.py $cc $region upload }
}
Step 'apex index + deploy' { Set-Location "$root\CM-KG\DOOR\apex"; python build_index.py; $env:CLOUDFLARE_API_TOKEN = (Get-Content "$root\AGENT KEYS\cloudflare-d1.txt" -TotalCount 1).Trim(); npx wrangler deploy 2>&1 | Select-String 'Uploaded|error'; Remove-Item Env:CLOUDFLARE_API_TOKEN }
Step 'numbers log line + surfaces re-render' { Set-Location $rails; python numbers_log.py $cc; Set-Location "$root\CM-KG\ESTATE"; $env:CLOUDFLARE_API_TOKEN = (Get-Content "$root\AGENT KEYS\cloudflare-d1.txt" -TotalCount 1).Trim(); npx wrangler deploy 2>&1 | Select-String 'Uploaded|error'; Remove-Item Env:CLOUDFLARE_API_TOKEN }
Step 'snapshot surfaces to the pond' { Set-Location $rails; python snapshot_surfaces.py $cc }
"DONE $cc $(Get-Date -Format 'yyyy-MM-dd HH:mm')" | Tee-Object -FilePath $log -Append
