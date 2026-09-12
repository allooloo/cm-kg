# jp Width 1 build-day chain (ORDER-017 re-cut, 2026-09-12): EDINET daily documents lists over 12 months, cut per issuer, assemble. Pond-native; raw = open width1 drop.
Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
function Step($name, $cmd) { "== $name $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log; & $cmd 2>&1 | Out-File -Append raw\build.log }
Step 'edinet_events' { python edinet_events.py }
Step 'assemble' { python assemble_disclosure.py }
"== WIDTH1 DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
