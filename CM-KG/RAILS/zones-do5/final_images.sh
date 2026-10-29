#!/bin/sh
# DAY ORDER 5 close: the fleet image of record carries today's tree (roster with region + duty, estate, apex, ECO data), every job moved to it; eco-refresh
# image with the duty hunt and the spec generator; Jersey re-run so its records carry the halt flag (its shim was broken on the night run); capacity snapshot;
# one manual digest run on the fleet tag to prove the capacity, drift and market-count blocks.
H=/c/ALLOOLOO/CM-KG/RAILS/zones-do5; S='C:\Users\matth\AppData\Local\Temp\claude\C--bpc-agent\487034dc-d9cf-4486-b1b7-3150b19ff9a0\scratchpad'
export AZURE_CONFIG_DIR="C:/ALLOOLOO/.azure" MSYS_NO_PATHCONV=1 PYTHONUTF8=1
T=0.34.14
python -I -X utf8 'C:\ALLOOLOO\CM-KG\RAILS\job\build_context.py' "$S\ctx$T" | tail -1
az acr build -r allooloocmkg -t cmkg-sweep:$T --no-logs "$S\ctx$T" -o none 2>&1 | grep -v WARNING | tail -1
for i in $(seq 1 60); do st=$(az acr task list-runs -r allooloocmkg --top 3 --query "[?outputImages[0].tag=='$T'].status | [0]" -o tsv); case "$st" in Running|Queued|"") sleep 20;; *) break;; esac; done; echo "image $T $st"; [ "$st" = Succeeded ] || exit 1
cd 'C:\ALLOOLOO\CM-KG\RAILS\job' && python -X utf8 -I provision_jobs.py upgrade $T nl ch fr de sg au uk ca jp kr hk us it es se dk no fi be ie at pl pt lu gr cz ky bm je in tw ae br mx apex 2>&1 | grep -v WARNING | sed 's/ · env changed.*//' | grep -c "-> $T" | sed "s/^/jobs moved to $T: /"
python -X utf8 -I provision_jobs.py digest $T 2>&1 | grep -v WARNING | tail -1
E=0.1.$(python -X utf8 -I -c "import subprocess,json;print(max(int(t.split('.')[-1]) for t in json.loads(subprocess.run(['az','acr','repository','show-tags','-n','allooloocmkg','--repository','eco-refresh','-o','json'],capture_output=True,text=True,shell=True).stdout) if t.startswith('0.1.'))+1)")
O=/c/Users/matth/AppData/Local/Temp/claude/C--bpc-agent/487034dc-d9cf-4486-b1b7-3150b19ff9a0/scratchpad/eco$E; rm -rf $O; MSYS_NO_PATHCONV=0 sh /c/ALLOOLOO/CM-KG/ECO/job/build_context.sh $O
az acr build -r allooloocmkg -t eco-refresh:$E --no-logs "$S\eco$E" -o none 2>&1 | grep -v WARNING | tail -1
for i in $(seq 1 60); do st=$(az acr task list-runs -r allooloocmkg --top 3 --query "[?outputImages[0].tag=='$E'].status | [0]" -o tsv); case "$st" in Running|Queued|"") sleep 20;; *) break;; esac; done; echo "eco image $E $st"
[ "$st" = Succeeded ] && (cd 'C:\ALLOOLOO\CM-KG\ECO\job' && python -X utf8 -I provision_eco.py $E 2>&1 | grep -v WARNING | tail -1)
JG=$(az containerapp job list --query "[?name=='cmkg-je-rail'].resourceGroup | [0]" -o tsv); R=$(az containerapp job start -n cmkg-je-rail -g $JG --query name -o tsv); echo "je halt rerun $R"
for i in $(seq 1 80); do s=$(az containerapp job execution show -n cmkg-je-rail -g $JG --job-execution-name $R --query properties.status -o tsv 2>/dev/null); case "$s" in Succeeded|Failed|Stopped) break;; esac; sleep 30; done; echo "je halt rerun $R $s"
python -X utf8 -I capacity_snapshot.py > /dev/null 2>&1 && echo "capacity snapshot written"
D=$(az containerapp job start -n cmkg-apex-digest -g allooloo-cmkg-eastus --query name -o tsv); echo "digest run $D"
for i in $(seq 1 60); do s=$(az containerapp job execution show -n cmkg-apex-digest -g allooloo-cmkg-eastus --job-execution-name $D --query properties.status -o tsv 2>/dev/null); case "$s" in Succeeded|Failed|Stopped) break;; esac; sleep 20; done; echo "digest run $D $s"
echo "FINAL END $(date -u +%H:%M)"
