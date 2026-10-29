#!/bin/sh
# DAY ORDER 5: (1) Jersey's job re-run once the fleet image carrying the 31-character loader fix and the tab rule (0.34.7) is on it; green -> nightly armed.
# (2) when row_chain.sh has ended, row_chain2.sh on list-chain2.txt (Mexico, then India).
H=/c/ALLOOLOO/CM-KG/RAILS/zones-do5; ST=$H/chain-status-row.txt; export AZURE_CONFIG_DIR="C:/ALLOOLOO/.azure" MSYS_NO_PATHCONV=1 PYTHONUTF8=1
until grep -q "cmkg-je-rail: .* -> 0.34.7" $H/log-job-tw.txt 2>/dev/null; do sleep 20; done
G=$(az containerapp job list --query "[?name=='cmkg-je-rail'].resourceGroup | [0]" -o tsv); E=$(az containerapp job start -n cmkg-je-rail -g $G --query name -o tsv); echo "je rerun $E"
for i in $(seq 1 120); do s=$(az containerapp job execution show -n cmkg-je-rail -g $G --job-execution-name $E --query properties.status -o tsv 2>/dev/null); case "$s" in Succeeded|Failed|Stopped) break;; esac; sleep 30; done
SG=$(az storage account list --query "[?name=='allooloocmkgjepond'].resourceGroup | [0]" -o tsv); K=$(az storage account keys list -n allooloocmkgjepond -g $SG --query [0].value -o tsv)
B=$(az storage blob list --account-name allooloocmkgjepond --account-key $K -c pond --prefix sweeps/ --query "[].name" -o tsv | tr '\n' ' ')
case "$s" in Succeeded) case "$B" in *held.txt*) echo "je HELD on rerun $E · $B" | tee -a $ST;; *done.json*) (cd 'C:\ALLOOLOO\CM-KG\RAILS\job' && python -X utf8 -I provision_jobs.py nightly je 2>&1 | grep -v WARNING); echo "je GREEN 0.34.7 · $(cat /c/ALLOOLOO/CM-KG/RAILS/eu-node/door-je.txt) · je run $E Succeeded (rerun: the first failed on the 31-character sheet name, fixed) · $(date -u +%H:%M)" | tee -a $ST;; *) echo "je NO DONE MARKER on rerun $E" | tee -a $ST;; esac;; *) echo "je NOT GREEN on rerun: $E $s" | tee -a $ST;; esac
until grep -q "^CHAIN END" $ST; do sleep 30; done
sh $H/row_chain2.sh $H/list-chain2.txt > $H/log-chain2.txt 2>&1
