# kr Width 1 build-day chain (ORDER-017 re-cut, 2026-09-12): DART filings per corp code over 12 months, then assemble. Pond-native; raw = open width1 drop.
Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'; $env:THREADS = '3'
function Step($name, $cmd) { "== $name $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log; & $cmd 2>&1 | Out-File -Append raw\build.log }
Step 'dart_events' { python dart_events.py }
Step 'assemble' { python assemble_disclosure.py }
"== WIDTH1 DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
