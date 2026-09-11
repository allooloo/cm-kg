# CM-KG rail — Australia passes 2 (Fill) and 3 (Confirm), run after the Width 1 weekly refresh (see CM-KG\RAILS\au-weekly.ps1). Pond-native; skips on the node lock.
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\au-cm-kg\.lock') { 'au-cm-kg locked (build order in flight): refresh skipped'; exit 0 }
python ..\pond_open.py au-cm-kg au-fill-confirm fill-confirm
$log = Join-Path $PSScriptRoot ('raw\refresh-' + (Get-Date -Format 'yyyy-MM-dd') + '.log')
function Step($name, $cmd) { "== $name $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append; & $cmd 2>&1 | Tee-Object -FilePath $log -Append }
Step 'Grok live layer (7 days)' { $env:LIVE_HOURS = '168'; $env:LIVE_MAX_ISSUERS = '200'; python grok_live.py }
Step 'Width 1 assemble with the live layer' { Push-Location ..\au-width1; $env:WINDOW_DAYS = '7'; python assemble_disclosure.py; Pop-Location }
Step 'aliases' { $env:THREADS = '5'; python alias_sources.py }
Step 'annual reports + Appendix 4E/4D (ASX PDFs)' { $env:THREADS = '4'; python annual_reports.py }
Step 'ChatGPT batch submit' { python chatgpt_batch.py submit }
Step 'Gemini AGM / registry' { $env:THREADS = '6'; python gemini_agm.py }
Step 'Perplexity (agent, low)' { $env:THREADS = '4'; $env:PPLX_MAX = '100'; python perplexity_pages.py }
Step 'Mistral non-English' { python mistral_reads.py }
Step 'rematch' { $env:THREADS = '4'; python rematch.py }
Step 'ChatGPT batch collect (waits up to 6 h)' { $t = 0; do { $r = python chatgpt_batch.py collect; if ($r -match 'ALL COLLECTED') { break }; Start-Sleep -Seconds 600; $t += 10 } while ($t -lt 360) }
Step 'confirm' { $env:THREADS = '6'; python confirm.py }
Step 'conflict adjudication' { python conflict_adjudicate.py }
Step 'rebuild issuers' { python rebuild_issuers.py }
Step 'rebuild disclosure' { python rebuild_disclosure.py }
Step 'spend' { python spend.py }
"DONE $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append
