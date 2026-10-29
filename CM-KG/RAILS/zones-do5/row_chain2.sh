#!/bin/sh
# row_chain2.sh — NODE-ROW follow-on (DAY ORDER 5, 2026-10-24): the row_chain.sh green rule for nodes whose pond lands after the first chain started
# (Mexico once BMV answered; India once its harvest assembles). The node list comes from a file (lines "cc region MIC/ISIN ISIN name_with_underscores");
# the tags come from the registry (next cmkg-sweep and eco-refresh tags), and the jobs moved with each image are the nodes that have a job, read from Azure.
# Run it only after row_chain.sh has ended (one image build and fleet move at a time). Usage: sh row_chain2.sh <list file>
H=/c/ALLOOLOO/CM-KG/RAILS/zones-do5; ST=$H/chain-status-row.txt
export AZURE_CONFIG_DIR="C:/ALLOOLOO/.azure" PYTHONUTF8=1 PYTHONIOENCODING=utf-8
nexttag() { python -X utf8 -I -c "import subprocess,json,sys;r=sys.argv[1];v=sorted(tuple(map(int,t.split('.'))) for t in json.loads(subprocess.run(['az','acr','repository','show-tags','-n','allooloocmkg','--repository',r,'-o','json'],capture_output=True,text=True,shell=True).stdout) if t.count('.')==2 and t.replace('.','').isdigit() and (r!='eco-refresh' or t.startswith('0.1.')));print('%d.%d.%d'%(v[-1][0],v[-1][1],v[-1][2]+1))" "$1"; }
while read CC REGION EX ISIN NAME; do
  [ -z "$CC" ] && continue; NAME=$(echo "$NAME" | tr _ " "); grep -q "^$CC GREEN" $ST 2>/dev/null && continue
  TAG=$(nexttag cmkg-sweep); ECO=$(nexttag eco-refresh); echo "== $CC $(date -u +%H:%M) tag $TAG"
  [ -f /c/ALLOOLOO/CM-KG/POND/$CC-cm-kg/assembled/2026-10-24/build.json ] || { echo "$CC NO POND (harvest not assembled)" | tee -a $ST; continue; }
  sh $H/row_close.sh $CC $REGION $EX $ISIN "$NAME" > $H/log-close-$CC.txt 2>&1 < /dev/null || { echo "$CC CLOSE FAILED (log-close-$CC.txt)" | tee -a $ST; continue; }
  LIVE="it es se dk no fi be ie at pl pt lu gr cz $(MSYS_NO_PATHCONV=1 az containerapp job list --query "[?starts_with(name,'cmkg-') && ends_with(name,'-rail')].name" -o tsv < /dev/null | sed -n 's/^cmkg-\(ky\|bm\|je\|in\|tw\|ae\|br\|mx\)-rail$/\1/p' | tr '\n' ' ') $CC"
  sh $H/row_job.sh $CC $TAG $ECO "$LIVE" > $H/log-job-$CC.txt 2>&1 < /dev/null
  RUN=$(grep "^$CC run " $H/log-job-$CC.txt | tail -1)
  G=$(MSYS_NO_PATHCONV=1 az storage account list --query "[?name=='allooloocmkg${CC}pond'].resourceGroup | [0]" -o tsv < /dev/null)
  K=$(MSYS_NO_PATHCONV=1 az storage account keys list -n allooloocmkg${CC}pond -g $G --query [0].value -o tsv < /dev/null)
  B=$(MSYS_NO_PATHCONV=1 az storage blob list --account-name allooloocmkg${CC}pond --account-key $K -c pond --prefix sweeps/ --query "[].name" -o tsv < /dev/null | tr '\n' ' ')
  case "$RUN" in *Succeeded*) ;; *) echo "$CC NOT GREEN: $RUN · $B" | tee -a $ST; continue;; esac
  case "$B" in *held.txt*) echo "$CC HELD: $RUN · $B" | tee -a $ST; continue;; *done.json*) ;; *) echo "$CC NO DONE MARKER: $RUN · $B" | tee -a $ST; continue;; esac
  (cd 'C:\ALLOOLOO\CM-KG\RAILS\job' && MSYS_NO_PATHCONV=1 python -X utf8 -I provision_jobs.py nightly $CC < /dev/null 2>&1 | grep -v WARNING) >> $H/log-job-$CC.txt
  echo "$CC GREEN $TAG eco $ECO · $(cat /c/ALLOOLOO/CM-KG/RAILS/eu-node/door-$CC.txt) · $RUN · $(date -u +%H:%M)" | tee -a $ST
done < "$1"
echo "CHAIN2 END $(date -u +%H:%M)" | tee -a $ST
