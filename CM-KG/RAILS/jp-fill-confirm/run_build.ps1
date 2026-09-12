# jp Fill pass, part 2 (ORDER-017 re-cut, 2026-09-12). Reading order: Gemini reads the Japanese report windows as primary; Perplexity (agent, fast) is the search layer; Grok second (live layer); Mistral review only.
$ErrorActionPreference = 'Continue'; Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
function Step($name, $cmd) { "== $name $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log; & $cmd 2>&1 | Out-File -Append raw\build.log }
Step 'gemini reads' { $env:THREADS = '6'; python gemini_reads.py }
Step 'perplexity' { $env:THREADS = '4'; $env:PPLX_MAX = '4000'; python perplexity_pages.py }
Step 'grok live' { $env:LIVE_HOURS = '168'; $env:LIVE_MAX_ISSUERS = '40'; python grok_live.py }
Step 'mistral review' { $env:THREADS = '4'; python mistral_reads.py }
Step 'rebuild issuers' { python rebuild_issuers.py }
Step 'rebuild disclosure' { python rebuild_disclosure.py }
Step 'spend' { python spend.py }
"== FILL CHAIN DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
