# Fill pass, second final (ORDER-017 re-cut): after the Perplexity rerun — Mistral reviews the newly located pages (resumable), then the rebuilds from the Width 0 base workbook and the spend line.
$ErrorActionPreference = 'Continue'; Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
function Step($name, $cmd) { "== $name $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log; & $cmd 2>&1 | Out-File -Append raw\build-final2.log }
while (-not (Select-String -Path raw\build.log -Pattern 'PERPLEXITY RERUN DONE' -Quiet)) { Start-Sleep 60 }
Step 'mistral review (pages)' { $env:THREADS = '4'; python mistral_reads.py }
Step 'rebuild issuers' { $env:BASE_XLSX = 'C:\ALLOOLOO\CM-KG\POND\jp-cm-kg\assembled\2026-09-12-2\jp-issuers.xlsx'; python rebuild_issuers.py }
Step 'rebuild disclosure' { python rebuild_disclosure.py }
Step 'spend' { python spend.py }
"== FINAL2 DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
