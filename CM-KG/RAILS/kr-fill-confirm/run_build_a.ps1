# kr Fill pass, part 2a (ORDER-017 re-cut): the search layer — Perplexity (agent, fast) — independent of the report reads.
$ErrorActionPreference = 'Continue'; Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
function Step($name, $cmd) { "== $name $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log; & $cmd 2>&1 | Out-File -Append raw\build-a.log }
Step 'perplexity' { $env:THREADS = '4'; $env:PPLX_MAX = '4000'; python perplexity_pages.py }
Step 'grok live' { $env:LIVE_HOURS = '168'; $env:LIVE_MAX_ISSUERS = '40'; python grok_live.py }
"== CHAIN A DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
