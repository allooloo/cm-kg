# CM-KG weekly sweep per node (ORDER-020 §10, re-armed Sept 12 2026):
#   harvest -> immutable pond drop -> regional store reload -> apex list_nodes updates -> surfaces re-render -> one line to NODE-SURFACES.md NUMBERS LOG.
# Usage: powershell -File sweep_node.ps1 <cc> <azure-region>      e.g. sweep_node.ps1 uk uksouth
# Skips on the global BUILD lock (CM-KG\POND\.build-lock) or the node lock (POND\<cc>-cm-kg\.lock). Nothing deleted; new drops beside old.
param([Parameter(Mandatory=$true)][string]$cc, [Parameter(Mandatory=$true)][string]$region)
$ErrorActionPreference = 'Continue'
$env:AZURE_CONFIG_DIR = 'C:\ALLOOLOO\.azure'   # STARTHERE 2026-09-19: this root's login directories
$env:GH_CONFIG_DIR = 'C:\ALLOOLOO\.gh'
$root = 'C:\ALLOOLOO'; $rails = "$root\CM-KG\RAILS"
$log = "$root\CM-KG\SWEEPS\$cc-$(Get-Date -Format 'yyyy-MM-dd').log"; New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
function Step($name, $cmd) { "== $name $(Get-Date -Format 'yyyy-MM-dd HH:mm')" | Tee-Object -FilePath $log -Append; & $cmd 2>&1 | Tee-Object -FilePath $log -Append }
if (Test-Path "$root\CM-KG\POND\.build-lock") { "global BUILD lock set: sweep skipped" | Tee-Object -FilePath $log -Append; exit 0 }
if (Test-Path "$root\CM-KG\POND\$cc-cm-kg\.lock") { "$cc-cm-kg locked: sweep skipped" | Tee-Object -FilePath $log -Append; exit 0 }
$env:PYTHONIOENCODING = 'utf-8'
# ORDER-024 (2026-09-18): the scheduled task has no stdin — npx's install prompt and wrangler's metrics prompt hung the nl apex step for hours on the 09-18 run; --yes + CI + no metrics keep every wrangler call non-interactive.
$env:WRANGLER_SEND_METRICS = 'false'; $env:CI = '1'
# ORDER-027 A1 (CEO 2026-10-17): a node's as-of is the sweep's MARKET DATE — the Friday the weekly task is armed for — never the UTC moment the node started
# (supersedes the Sept 12 2026 sweep-start-in-UTC rule). sweep_all.ps1 sets SWEEP_MARKET_DATE once per run; a lone node run takes the Friday on or before today.
if ($env:SWEEP_MARKET_DATE) { $sweepStartUtc = $env:SWEEP_MARKET_DATE } else { $d = Get-Date; $sweepStartUtc = $d.AddDays(-((([int]$d.DayOfWeek) - 5 + 7) % 7)).ToString('yyyy-MM-dd') }
"sweep market date $sweepStartUtc" | Tee-Object -FilePath $log -Append
if ($cc -eq 'us') {
  # the United States rail is the East US container job; one run, wait for it, then the estate steps
  Step 'us job start' { az containerapp job start -g allooloo-cmkg-eastus -n cmkg-us-rail -o none }
  Step 'us job wait' { $deadline = (Get-Date).AddHours(4); do { Start-Sleep -Seconds 120; $st = az containerapp job execution list -g allooloo-cmkg-eastus -n cmkg-us-rail --query "[0].properties.status" -o tsv } while ($st -eq 'Running' -and (Get-Date) -lt $deadline); "us job status: $st" }
  # ORDER-027 A1: the job stamps its own date from the container clock (UTC); the door's facts and nodes are re-stamped to the market date
  # CEO standing line 2 (2026-10-17): forward-only door — the job publishes inside its container, so the gate compares after it and restores the last good index on a drop
  Step 'forward-only gate (after job)' { Set-Location "$rails\door"; python door_gate.py us eastus $sweepStartUtc --after-job; "gate exit $LASTEXITCODE" }; $gate = $LASTEXITCODE
  if ($gate -eq 0) { Step 'us as-of = market date' { Set-Location "$rails\door"; python restamp_asof.py us eastus $sweepStartUtc } } else { "us door HELD (gate exit $gate): as-of not advanced; flag in CM-KG\SWEEPS for the machine half" | Tee-Object -FilePath $log -Append }
} else {
  Step 'harvest (Width 1 refresh, 7-day window, new pond drop)' { Set-Location "$rails\$cc-width1"; & ".\run_refresh.ps1"; "harvest rail exit $LASTEXITCODE" }
  if ($LASTEXITCODE -ne 0) { "DONE $cc STOPPED: harvest rail exit $LASTEXITCODE (close-out 2026-10-10: the rail's exit code decides; door, store and apex left as they were) $(Get-Date -Format 'yyyy-MM-dd HH:mm')" | Tee-Object -FilePath $log -Append; exit $LASTEXITCODE }
  Step 'door data' { Set-Location "$rails\door"; Set-Item -Path ("Env:AS_OF_" + $cc.ToUpper()) -Value $sweepStartUtc; python load_nodes.py $cc }   # the node's date on the wire moves with the sweep (drop date = this sweep's drop)
  # CEO standing line 2 (2026-10-17): forward-only door — fewer records or events than the door serves now = HOLD: pond drops still upload, the door keeps its last good data, the new index/facts/nodes go beside (door-held/<market date>/), one flag file for the machine half
  Step 'forward-only gate' { Set-Location "$rails\door"; python door_gate.py $cc $region $sweepStartUtc; "gate exit $LASTEXITCODE" }; $gate = $LASTEXITCODE
  if ($gate -ne 0) { $env:DOOR_HOLD = $sweepStartUtc } else { Remove-Item Env:DOOR_HOLD -ErrorAction SilentlyContinue }
  Step 'regional store reload' { Set-Location "$root\AZURE"; python provision_region.py $cc $region upload }
  Remove-Item Env:DOOR_HOLD -ErrorAction SilentlyContinue
}
Step 'apex index + deploy' { Set-Location "$root\CM-KG\DOOR\apex"; python build_index.py; $env:CLOUDFLARE_API_TOKEN = (Get-Content "$root\AGENT KEYS\cloudflare-d1.txt" -TotalCount 1).Trim(); npx --yes wrangler deploy 2>&1 | Select-String 'Uploaded|error'; Remove-Item Env:CLOUDFLARE_API_TOKEN }
Step 'numbers log line + surfaces re-render' { Set-Location $rails; python numbers_log.py $cc; Set-Location "$root\CM-KG\ESTATE"; $env:CLOUDFLARE_API_TOKEN = (Get-Content "$root\AGENT KEYS\cloudflare-d1.txt" -TotalCount 1).Trim(); npx --yes wrangler deploy 2>&1 | Select-String 'Uploaded|error'; Remove-Item Env:CLOUDFLARE_API_TOKEN }
Step 'snapshot surfaces to the pond' { Set-Location $rails; python snapshot_surfaces.py $cc }
"DONE $cc $(Get-Date -Format 'yyyy-MM-dd HH:mm')" | Tee-Object -FilePath $log -Append
