# kr Fill pass: Gemini reads the report windows as the document shards deliver them (resumable), until the shards report DONE, then one final pass.
Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'; $env:THREADS = '6'
function Done { (Select-String -Path raw\build.log -Pattern 'DOCS DONE' -Quiet) -or ((Select-String -Path raw\build.log -Pattern 'shard [0-9]/6 DONE' -AllMatches | Measure-Object).Count -ge 6) }
do { "== gemini reads (loop) $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log; python gemini_reads.py 2>&1 | Out-File -Append raw\build-b.log; if (-not (Done)) { Start-Sleep 120 } } while (-not (Done))
"== gemini reads (final) $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log; python gemini_reads.py 2>&1 | Out-File -Append raw\build-b.log
"== GEMINI DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
