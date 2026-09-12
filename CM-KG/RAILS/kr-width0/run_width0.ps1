# kr Width 0 chain (ORDER-017 re-cut, 2026-09-12): KIND list + DART corp codes + DART company profiles. Pond-native; raw = open width0 drop.
Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'; $env:THREADS = '3'
function Step($name, $cmd) { "== $name $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log; & $cmd 2>&1 | Out-File -Append raw\build.log }
Step 'fetch_sources' { python fetch_sources.py }
"== FETCH DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
