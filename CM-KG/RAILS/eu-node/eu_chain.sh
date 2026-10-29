#!/bin/sh
# eu_chain.sh — NODE-EU-04…14 (DAY ORDER 4, 2026-10-24): the remaining European nodes in order, each to green close before the next.
# Per node: eu_close.sh (door data, region, door, apex, ECO) -> eu_job.sh (image tag = version, job, first run, every job moved to the tag, eco-refresh)
# -> green = the run Succeeded AND published (done.json, no held.txt) -> nightly cron armed. The first node that is not green stops the chain.
# One line per node to chain-status.txt beside. Usage: sh eu_chain.sh <first image minor> <first eco patch>   (e.g. 9 12 -> 0.33.9 / 0.1.12)
M="$1"; P="$2"; H=/c/ALLOOLOO/CM-KG/RAILS/eu-node; LIVE="it es se"; ST=$H/chain-status.txt
export AZURE_CONFIG_DIR="C:/ALLOOLOO/.azure" PYTHONUTF8=1 PYTHONIOENCODING=utf-8
while read CC REGION EX ISIN NAME; do
  [ -z "$CC" ] && continue
  NAME=$(echo "$NAME" | tr _ " "); LIVE="$LIVE $CC"; grep -q "^$CC GREEN" $ST && continue; TAG=0.33.$M; ECO=0.1.$P; M=$((M+1)); P=$((P+1))
  echo "== $CC $(date -u +%H:%M) tag $TAG"
  sh $H/eu_close.sh $CC $REGION $EX $ISIN "$NAME" > $H/log-close-$CC.txt 2>&1 < /dev/null || { echo "$CC CLOSE FAILED (log-close-$CC.txt)" | tee -a $ST; exit 1; }
  sh $H/eu_job.sh $CC $TAG $ECO "$LIVE" > $H/log-job-$CC.txt 2>&1 < /dev/null
  RUN=$(grep "^$CC run " $H/log-job-$CC.txt | tail -1)
  K=$(MSYS_NO_PATHCONV=1 az storage account keys list -n allooloocmkg${CC}pond -g allooloo-cmkg-$REGION --query [0].value -o tsv < /dev/null)
  B=$(MSYS_NO_PATHCONV=1 az storage blob list --account-name allooloocmkg${CC}pond --account-key $K -c pond --prefix sweeps/ --query "[].name" -o tsv < /dev/null | tr '\n' ' ')
  case "$RUN" in *Succeeded*) ;; *) echo "$CC NOT GREEN: $RUN · $B" | tee -a $ST; exit 1;; esac
  case "$B" in *held.txt*) echo "$CC HELD: $RUN · $B" | tee -a $ST; exit 1;; *done.json*) ;; *) echo "$CC NO DONE MARKER: $RUN · $B" | tee -a $ST; exit 1;; esac
  (cd 'C:\ALLOOLOO\CM-KG\RAILS\job' && MSYS_NO_PATHCONV=1 python -X utf8 -I provision_jobs.py nightly $CC < /dev/null 2>&1 | grep -v WARNING) >> $H/log-job-$CC.txt
  echo "$CC GREEN $TAG eco $ECO · $(cat $H/door-$CC.txt) · $RUN · $(date -u +%H:%M)" | tee -a $ST
done <<EOF
dk swedencentral XCSE/DK0062498333 DK0062498333 NOVO_NORDISK_B
no norwayeast XOSL/NO0010096985 NO0010096985 EQUINOR
fi swedencentral XHEL/FI0009000681 FI0009000681 NOKIA
be belgiumcentral XBRU/BE0974293251 BE0974293251 AB_INBEV
ie northeurope XMSM/IE0004906560 IE0004906560 KERRY_GROUP
at austriaeast WBAH/AT0000652011 AT0000652011 ERSTE_GROUP
pl polandcentral XWAR/PLPKO0000016 PLPKO0000016 PKO_BP
pt spaincentral XLIS/PTEDP0AM0009 PTEDP0AM0009 EDP
lu belgiumcentral XLUX/LU0569974404 LU0569974404 APERAM
gr italynorth XATH/GRS003003035 GRS003003035 NATIONAL_BANK_OF_GREECE
cz austriaeast XPRA/CZ0005112300 CZ0005112300 CEZ
EOF
echo "CHAIN END $(date -u +%H:%M)" | tee -a $ST
