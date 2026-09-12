# kr Fill pass, part 1 (ORDER-017 re-cut): the auditor from DART's structured endpoint. Pond-native; raw = open fill-confirm drop.
Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'; $env:THREADS = '3'
"== dart_auditor $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
python dart_auditor.py 2>&1 | Out-File -Append raw\build.log
"== AUDITOR DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
