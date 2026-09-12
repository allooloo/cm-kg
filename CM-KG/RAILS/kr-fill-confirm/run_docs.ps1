# kr Fill pass, part 1b (ORDER-017 re-cut): the 사업보고서 main documents to Korean text windows (DART document API is slow: three shards of four threads). Waits for the auditor pull.
Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
while (-not (Select-String -Path raw\build.log -Pattern 'AUDITOR DONE' -Quiet)) { Start-Sleep 20 }
"== dart_docs $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
$jobs = @()
foreach ($i in 0..2) { $jobs += Start-Process powershell -PassThru -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-Command',"Set-Location '$PSScriptRoot'; `$env:PYTHONIOENCODING='utf-8'; `$env:THREADS='4'; `$env:SHARD='$i/3'; python dart_docs.py 2>&1 | Out-File -Append raw\docs-shard$i.log" }
$jobs | Wait-Process
"== DOCS DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
