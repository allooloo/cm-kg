# ORDER-018 — one region end to end: storage -> upload -> app -> bind (certificate by TXT). The flip (records to the new origin) runs separately once the binding shows SniEnabled.
param([string]$cc, [string]$region)
Set-Location 'C:\ALLOOLOO\AZURE'; $env:PYTHONIOENCODING = 'utf-8'
$log = "C:\ALLOOLOO\AZURE\region-$cc.log"
foreach ($step in 'storage', 'upload', 'app', 'bind') {
  "== $cc $region $step $(Get-Date -Format 'HH:mm')" | Out-File -Append $log
  python provision_region.py $cc $region $step 2>&1 | Out-File -Append $log
}
"== $cc $region CHAIN DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append $log
