# ORDER-012 build-day chain, part 2 (2026-09-11): Confirm and the rebuilds, run while the Grok live layer finishes in parallel (its events are merged by a later rebuild_disclosure).
$ErrorActionPreference = 'Continue'; Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
function Step($name, $cmd) { "== $name $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build2.log; & $cmd 2>&1 | Out-File -Append raw\build2.log }
Step 'confirm' { $env:THREADS = '6'; python confirm.py }
Step 'conflict adjudication' { python conflict_adjudicate.py }
Step 'rebuild issuers' { python rebuild_issuers.py }
Step 'rebuild disclosure' { python rebuild_disclosure.py }
Step 'spend' { python spend.py }
"== CHAIN2 DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build2.log
