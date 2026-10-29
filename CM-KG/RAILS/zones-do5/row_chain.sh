#!/bin/sh
# row_chain.sh — NODE-ROW-02…09 (DAY ORDER 5, 2026-10-24): one ROW node at a time, the NODE-EU chain's green rule (eu_chain.sh):
#   pond assembled (eu_node.py, harvested beforehand) -> row_close.sh -> row_job.sh (image tag = version, job, first run, fleet moved, eco image)
#   -> green = the run Succeeded AND published (done.json, no held.txt) -> provision_jobs.py nightly <cc> (02:00 local standard time).
# A node that is not green is flagged in chain-status-row.txt and the chain carries on (the order: flag it and carry on). Usage: sh row_chain.sh
H=/c/ALLOOLOO/CM-KG/RAILS/zones-do5; ST=$H/chain-status-row.txt; M=4; P=27; LIVE="it es se dk no fi be ie at pl pt lu gr cz ky"
export AZURE_CONFIG_DIR="C:/ALLOOLOO/.azure" PYTHONUTF8=1 PYTHONIOENCODING=utf-8
while read CC REGION EX ISIN NAME; do
  [ -z "$CC" ] && continue; NAME=$(echo "$NAME" | tr _ " "); grep -q "^$CC GREEN" $ST 2>/dev/null && { LIVE="$LIVE $CC"; continue; }
  TAG=0.34.$M; ECO=0.1.$P; M=$((M+1)); P=$((P+1)); echo "== $CC $(date -u +%H:%M) tag $TAG"
  for i in $(seq 1 240); do [ -f /c/ALLOOLOO/CM-KG/POND/$CC-cm-kg/assembled/2026-10-24/build.json ] && break; sleep 30; done
  [ -f /c/ALLOOLOO/CM-KG/POND/$CC-cm-kg/assembled/2026-10-24/build.json ] || { echo "$CC NO POND (harvest not assembled)" | tee -a $ST; continue; }
  sh $H/row_close.sh $CC $REGION $EX $ISIN "$NAME" > $H/log-close-$CC.txt 2>&1 < /dev/null || { echo "$CC CLOSE FAILED (log-close-$CC.txt)" | tee -a $ST; continue; }
  LIVE="$LIVE $CC"
  sh $H/row_job.sh $CC $TAG $ECO "$LIVE" > $H/log-job-$CC.txt 2>&1 < /dev/null
  RUN=$(grep "^$CC run " $H/log-job-$CC.txt | tail -1)
  G=$(MSYS_NO_PATHCONV=1 az storage account list --query "[?name=='allooloocmkg${CC}pond'].resourceGroup | [0]" -o tsv < /dev/null)
  K=$(MSYS_NO_PATHCONV=1 az storage account keys list -n allooloocmkg${CC}pond -g $G --query [0].value -o tsv < /dev/null)
  B=$(MSYS_NO_PATHCONV=1 az storage blob list --account-name allooloocmkg${CC}pond --account-key $K -c pond --prefix sweeps/ --query "[].name" -o tsv < /dev/null | tr '\n' ' ')
  case "$RUN" in *Succeeded*) ;; *) echo "$CC NOT GREEN: $RUN · $B" | tee -a $ST; continue;; esac
  case "$B" in *held.txt*) echo "$CC HELD: $RUN · $B" | tee -a $ST; continue;; *done.json*) ;; *) echo "$CC NO DONE MARKER: $RUN · $B" | tee -a $ST; continue;; esac
  (cd 'C:\ALLOOLOO\CM-KG\RAILS\job' && MSYS_NO_PATHCONV=1 python -X utf8 -I provision_jobs.py nightly $CC < /dev/null 2>&1 | grep -v WARNING) >> $H/log-job-$CC.txt
  echo "$CC GREEN $TAG eco $ECO · $(cat /c/ALLOOLOO/CM-KG/RAILS/eu-node/door-$CC.txt) · $RUN · $(date -u +%H:%M)" | tee -a $ST
done <<EOF
bm eastus XBDA/BMG0772R2087 BMG0772R2087 The_Bank_of_N.T._Butterfield_&_Son_Limited
je uksouth XCIE/JE00BTGQPZ41 JE00BTGQPZ41 Broadgate_REIT
in centralindia XNSE/INE002A01018 INE002A01018 Reliance_Industries_Limited
tw eastasia XTAI/TW0002330008 TW0002330008 台灣積體電路製造股份有限公司
ae uaenorth XDFM/AEE000301011 AEE000301011 Emaar_Properties_PJSC
br brazilsouth BVMF/BRPETRACNPR6 BRPETRACNPR6 PETROLEO_BRASILEIRO_S.A._PETROBRAS
EOF
echo "CHAIN END $(date -u +%H:%M)" | tee -a $ST
