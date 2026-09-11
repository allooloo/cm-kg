# CM-KG rail — United Kingdom passes 2 (Fill) and 3 (Confirm), run after the Width 1 weekly refresh (see CM-KG\RAILS\uk-weekly.ps1).
# Grok live layer (7-day window), bodies for new results/AGM announcements, ChatGPT batch submit + collect, Gemini for issuers still without an AGM event
# or registrar, Mistral for non-English announcements, confirm for issuers whose fields changed, then both rebuilds and the spend line.
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
# pond rule: skip on the node lock; open a new dated drop (raw\ becomes a junction to it); nothing is deleted or moved
if (Test-Path 'C:\ALLOOLOO\CM-KG\POND\uk-cm-kg\.lock') { 'uk-cm-kg locked (build order in flight): refresh skipped'; exit 0 }
python ..\pond_open.py uk-cm-kg uk-fill-confirm fill-confirm
$log = Join-Path $PSScriptRoot ('raw\refresh-' + (Get-Date -Format 'yyyy-MM-dd') + '.log')
function Step($name, $cmd) { "== $name $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append; & $cmd 2>&1 | Tee-Object -FilePath $log -Append }
Step 'Grok live layer (7 days)' { $env:LIVE_HOURS = '168'; $env:LIVE_MAX_ISSUERS = '200'; python grok_live.py }
Step 'Width 1 assemble with the live layer' { Push-Location ..\uk-width1; $env:WINDOW_DAYS = '7'; python assemble_disclosure.py; Pop-Location }
Step 'aliases' { $env:THREADS = '5'; python alias_sources.py }
Step 'bodies' { $env:THREADS = '4'; python fetch_bodies.py }
Step 'ChatGPT batch submit (results)' { python chatgpt_batch.py submit_results }
Step 'Gemini AGM / registrar' { $env:THREADS = '6'; python gemini_agm.py }
Step 'Mistral non-English' { python mistral_reads.py }
Step 'ChatGPT batch collect (waits up to 6 h)' { $t = 0; do { $r = python chatgpt_batch.py collect; if ($r -match 'ALL COLLECTED') { break }; Start-Sleep -Seconds 600; $t += 10 } while ($t -lt 360) }
Step 'confirm' { $env:THREADS = '6'; python confirm.py }
Step 'rebuild issuers' { python rebuild_issuers.py }
Step 'rebuild disclosure' { python rebuild_disclosure.py }
Step 'spend' { python spend.py }
"DONE $(Get-Date -Format 'yyyy-MM-dd')" | Tee-Object -FilePath $log -Append
