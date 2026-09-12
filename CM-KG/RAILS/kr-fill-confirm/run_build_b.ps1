# kr Fill pass, part 2b (ORDER-017 re-cut): after the document reads and the Width 1 assembly — Gemini (Korean, primary), Grok live, Mistral review, rebuilds, spend.
$ErrorActionPreference = 'Continue'; Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
function Step($name, $cmd) { "== $name $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log; & $cmd 2>&1 | Out-File -Append raw\build-b.log }
Step 'gemini reads' { $env:THREADS = '6'; python gemini_reads.py }
Step 'grok live' { $env:LIVE_HOURS = '168'; $env:LIVE_MAX_ISSUERS = '40'; python grok_live.py }
Step 'mistral review' { $env:THREADS = '4'; python mistral_reads.py }
Step 'rebuild issuers' { python rebuild_issuers.py }
Step 'rebuild disclosure' { python rebuild_disclosure.py }
Step 'spend' { python spend.py }
"== CHAIN B DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
