# CM-KG — the weekly sweep: all eleven nodes, one run, in order (CEO wrap of ORDER-020, Sept 12 2026). Nothing armed separately.
# SWEEP CLOCK (CEO, Sept 12 2026): starts after 16:00 Eastern Friday, all eleven markets closed — task fires 16:30 Eastern = 20:30 UTC (14:30 build-machine time, UTC-6, no daylight shift). Each node's as-of is its sweep start in UTC; uploads follow overnight.
# Each node runs sweep_node.ps1 (harvest -> drop -> store reload -> apex -> Numbers Log line -> re-render -> snapshot); a node lock skips that node.
# ORDER-024 (2026-09-18): the sweep rail carries its own Azure CLI login directory (C:\ALLOOLOO\.azure, logged in to the Allooloo tenant of record once) so the scheduled task never depends on the context an interactive session left behind — the same pattern as the separate gh config directories. Every child (sweep_node -> python -> az) inherits it; the tenant guard in provision_region.py / build_index.py stays.
$env:AZURE_CONFIG_DIR = 'C:\ALLOOLOO\.azure'
$env:GH_CONFIG_DIR = 'C:\ALLOOLOO\.gh'   # STARTHERE 2026-09-19: this root's GitHub login directory
$nodes = @(@('nl','westeurope'),@('ch','switzerlandnorth'),@('fr','francecentral'),@('de','germanywestcentral'),@('sg','southeastasia'),@('au','australiaeast'),@('uk','uksouth'),@('ca','canadacentral'),@('jp','japaneast'),@('kr','koreacentral'),@('us','eastus'))
$log = "C:\ALLOOLOO\CM-KG\SWEEPS\saturday-$(Get-Date -Format 'yyyy-MM-dd').log"
"SATURDAY SWEEP start $(Get-Date -Format 'yyyy-MM-dd HH:mm')" | Tee-Object -FilePath $log -Append
# close-out 2026-10-10: spend line per lab per run -> CM-KG\SPEND\SPEND.md (Tavily counter read at start, every lab summed at close)
# ORDER-027 A1: one market date per run — the Friday the task is armed for (the Friday on or before the start date); every node's as-of carries it
$d0 = Get-Date; $env:SWEEP_MARKET_DATE = $d0.AddDays(-((([int]$d0.DayOfWeek) - 5 + 7) % 7)).ToString('yyyy-MM-dd'); "market date $env:SWEEP_MARKET_DATE" | Tee-Object -FilePath $log -Append
$run = "sweep $(Get-Date -Format 'yyyy-MM-dd')"; $since = Get-Date -Format 'yyyy-MM-dd'; $env:PYTHONIOENCODING = 'utf-8'
python C:\ALLOOLOO\CM-KG\RAILS\spend_line.py --mark $run 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $log -Append
foreach ($n in $nodes) { "== $($n[0]) $(Get-Date -Format 'HH:mm')" | Tee-Object -FilePath $log -Append; powershell -NoProfile -ExecutionPolicy Bypass -File C:\ALLOOLOO\CM-KG\RAILS\sweep_node.ps1 $n[0] $n[1] 2>&1 | Tee-Object -FilePath $log -Append }
python C:\ALLOOLOO\CM-KG\RAILS\spend_line.py $run $since 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $log -Append
"SATURDAY SWEEP done $(Get-Date -Format 'yyyy-MM-dd HH:mm')" | Tee-Object -FilePath $log -Append
