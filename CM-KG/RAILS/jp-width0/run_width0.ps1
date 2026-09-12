# jp Width 0 chain (ORDER-017 re-cut, 2026-09-12): LEI match -> GLEIF records + ISINs -> assemble. Pond-native; raw = open width0 drop.
Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'; $env:THREADS = '3'
function Step($name, $cmd) { "== $name $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log; & $cmd 2>&1 | Out-File -Append raw\build.log }
Step 'lei_match' { python lei_match.py }
Step 'lei_records' { python lei_records.py }
Step 'assemble' { python assemble.py }
"== WIDTH0 DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
