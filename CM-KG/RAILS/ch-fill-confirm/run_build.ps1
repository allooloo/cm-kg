# ORDER-015 Part B build-day chain (2026-09-11), Switzerland. Reading order per the CEO rule for the European nodes: Perplexity (Agent API, low) → Grok → Mistral
# (translation and review only: confirms or disputes what the first two sourced; Mistral-only findings go to the Review tab, never to the record).
$ErrorActionPreference = 'Continue'; Set-Location $PSScriptRoot; $env:PYTHONIOENCODING = 'utf-8'
function Step($name, $cmd) { "== $name $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log; & $cmd 2>&1 | Out-File -Append raw\build.log }
Step 'aliases' { $env:THREADS = '5'; python alias_sources.py }
Step 'claude adjudicate' { python claude_adjudicate.py }
Step 'annual reports' { $env:THREADS = '4'; python annual_reports.py }
Step 'chatgpt submit' { python chatgpt_batch.py submit }
Step 'gemini agm' { $env:THREADS = '6'; python gemini_agm.py }
Step 'perplexity' { $env:THREADS = '4'; $env:PPLX_MAX = '400'; python perplexity_pages.py }
Step 'rematch' { $env:THREADS = '4'; python rematch.py }
Step 'grok live' { $env:LIVE_HOURS = '168'; $env:LIVE_MAX_ISSUERS = '40'; python grok_live.py }
Step 'mistral review' { python mistral_reads.py }
"== FILL CHAIN DONE $(Get-Date -Format 'HH:mm')" | Out-File -Append raw\build.log
