# CM-KG — the Saturday sweep: all eleven nodes, one run, in order (CEO wrap of ORDER-020, Sept 12 2026). Nothing armed separately.
# Each node runs sweep_node.ps1 (harvest -> drop -> store reload -> apex -> Numbers Log line -> re-render -> snapshot); a node lock skips that node.
$nodes = @(@('nl','westeurope'),@('ch','switzerlandnorth'),@('fr','francecentral'),@('de','germanywestcentral'),@('sg','southeastasia'),@('au','australiaeast'),@('uk','uksouth'),@('ca','canadacentral'),@('jp','japaneast'),@('kr','koreacentral'),@('us','eastus'))
$log = "C:\ALLOOLOO\CM-KG\SWEEPS\saturday-$(Get-Date -Format 'yyyy-MM-dd').log"
"SATURDAY SWEEP start $(Get-Date -Format 'yyyy-MM-dd HH:mm')" | Tee-Object -FilePath $log -Append
foreach ($n in $nodes) { "== $($n[0]) $(Get-Date -Format 'HH:mm')" | Tee-Object -FilePath $log -Append; powershell -NoProfile -ExecutionPolicy Bypass -File C:\ALLOOLOO\CM-KG\RAILS\sweep_node.ps1 $n[0] $n[1] 2>&1 | Tee-Object -FilePath $log -Append }
"SATURDAY SWEEP done $(Get-Date -Format 'yyyy-MM-dd HH:mm')" | Tee-Object -FilePath $log -Append
