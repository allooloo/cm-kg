Set-Location C:\ALLOOLOO\CM-KG\RAILS\jp-fill-confirm; $env:PYTHONIOENCODING = 'utf-8'; $env:THREADS = '3'; $env:SHARD = '3/6'
"== edinet_docs shard 3/6 $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
python edinet_docs.py 2>&1 | Out-File -Append ("raw\docs-shard-" + '3/6'.Replace('/', 'of') + ".log")
"== edinet_docs shard 3/6 DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
