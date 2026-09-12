# Fill pass, final part (ORDER-017 re-cut): waits for the Gemini loop and chain A (Perplexity, Grok), then Mistral review, the rebuilds and the spend line.
$ErrorActionPreference = 'Continue'; Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
function Step($name, $cmd) { "== $name $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log; & $cmd 2>&1 | Out-File -Append raw\build-final.log }
while (-not ((Select-String -Path raw\build.log -Pattern 'GEMINI DONE' -Quiet) -and (Select-String -Path raw\build.log -Pattern 'CHAIN A DONE' -Quiet))) { Start-Sleep 60 }
Step 'mistral review' { $env:THREADS = '4'; python mistral_reads.py }
Step 'rebuild issuers' { python rebuild_issuers.py }
Step 'rebuild disclosure' { python rebuild_disclosure.py }
Step 'spend' { python spend.py }
"== FINAL DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
