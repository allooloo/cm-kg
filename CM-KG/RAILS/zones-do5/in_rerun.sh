#!/bin/sh
# DAY ORDER 5: India's first nightly failed (BSE ListofScripData answered 403 to the Azure egress); roster.py now reuses the last sourced roster drop when an
# exchange list refuses. Image 0.34.12, the whole fleet moved to it (one fleet tag of record), India's job re-run, green -> nightly armed.
H=/c/ALLOOLOO/CM-KG/RAILS/zones-do5; ST=$H/chain-status-row.txt; S='C:\Users\matth\AppData\Local\Temp\claude\C--bpc-agent\487034dc-d9cf-4486-b1b7-3150b19ff9a0\scratchpad'
export AZURE_CONFIG_DIR="C:/ALLOOLOO/.azure" MSYS_NO_PATHCONV=1 PYTHONUTF8=1
python -I -X utf8 'C:\ALLOOLOO\CM-KG\RAILS\job\build_context.py' "$S\ctx03412" | tail -1
az acr build -r allooloocmkg -t cmkg-sweep:0.34.12 --no-logs "$S\ctx03412" -o none 2>&1 | grep -v WARNING | tail -1
for i in $(seq 1 60); do st=$(az acr task list-runs -r allooloocmkg --top 3 --query "[?outputImages[0].tag=='0.34.12'].status | [0]" -o tsv); case "$st" in Running|Queued|"") sleep 20;; *) break;; esac; done; echo "image 0.34.12 $st"; [ "$st" = Succeeded ] || exit 1
cd 'C:\ALLOOLOO\CM-KG\RAILS\job' && python -X utf8 -I provision_jobs.py upgrade 0.34.12 nl ch fr de sg au uk ca jp kr hk us it es se dk no fi be ie at pl pt lu gr cz ky bm je in tw ae br mx apex 2>&1 | grep -v WARNING | sed 's/ · env changed.*//'
python -X utf8 -I provision_jobs.py digest 0.34.12 2>&1 | grep -v WARNING | tail -1
G=allooloo-cmkg-centralindia; JG=$(az containerapp job list --query "[?name=='cmkg-in-rail'].resourceGroup | [0]" -o tsv)
E=$(az containerapp job start -n cmkg-in-rail -g $JG --query name -o tsv); echo "in rerun $E"
for i in $(seq 1 120); do s=$(az containerapp job execution show -n cmkg-in-rail -g $JG --job-execution-name $E --query properties.status -o tsv 2>/dev/null); case "$s" in Succeeded|Failed|Stopped) break;; esac; sleep 30; done
K=$(az storage account keys list -n allooloocmkginpond -g $G --query [0].value -o tsv); B=$(az storage blob list --account-name allooloocmkginpond --account-key $K -c pond --prefix sweeps/ --query "[].name" -o tsv | tr '\n' ' ')
case "$s" in Succeeded) case "$B" in *held.txt*) echo "in HELD on rerun $E · $B" | tee -a $ST;; *done.json*) python -X utf8 -I provision_jobs.py nightly in 2>&1 | grep -v WARNING; echo "in GREEN 0.34.12 · $(cat /c/ALLOOLOO/CM-KG/RAILS/eu-node/door-in.txt) · in run $E Succeeded (rerun: the first failed on BSE's 403 to cloud egress; roster falls back to the last sourced drop) · $(date -u +%H:%M)" | tee -a $ST;; *) echo "in NO DONE MARKER on rerun $E" | tee -a $ST;; esac;; *) echo "in NOT GREEN on rerun: $E $s · $B" | tee -a $ST;; esac
python -X utf8 -I capacity_snapshot.py > /dev/null 2>&1 && echo "capacity snapshot written"
