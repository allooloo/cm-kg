# jp Fill pass, part 1 (ORDER-017 re-cut): EDINET securities-report PDFs to text windows. Pond-native; raw = open fill-confirm drop.
Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'; $env:THREADS = '3'
"== edinet_docs $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
python edinet_docs.py 2>&1 | Out-File -Append raw\build.log
"== DOCS DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
