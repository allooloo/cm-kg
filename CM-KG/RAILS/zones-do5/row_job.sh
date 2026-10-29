#!/bin/sh
# row_job.sh — NODE-ROW (DAY ORDER 5, 2026-10-24), eu_job.sh with this session's scratchpad; from NODE-EU (DAY ORDER 4): the image, the node's job and its first run, on the current tree. Image tag = version.
#   build cmkg-sweep:<tag> from the tree (build_context.py) · create the node job on it · start it and wait · move every job (twelve nodes, the live
#   European nodes, the apex rail, both digests) to the tag · rebuild eco-refresh on its next tag. Usage: sh eu_job.sh <cc> <tag> <eco tag> "<live ccs>"
set -e
CC="$1"; TAG="$2"; ECOTAG="$3"; LIVE="$4"; S='C:\Users\matth\AppData\Local\Temp\claude\C--bpc-agent\487034dc-d9cf-4486-b1b7-3150b19ff9a0\scratchpad'
export AZURE_CONFIG_DIR="C:/ALLOOLOO/.azure" MSYS_NO_PATHCONV=1 PYTHONUTF8=1 PYTHONIOENCODING=utf-8
python -I -X utf8 'C:\ALLOOLOO\CM-KG\RAILS\job\build_context.py' "$S\ctx$TAG" | tail -1
az acr build -r allooloocmkg -t cmkg-sweep:$TAG --no-logs "$S\ctx$TAG" -o none 2>&1 | grep -v WARNING | tail -1 || true
for i in $(seq 1 60); do st=$(az acr task list-runs -r allooloocmkg --top 1 --query "[0].status" -o tsv); case "$st" in Running|Queued) sleep 20;; *) break;; esac; done; echo "image $TAG $st"; [ "$st" = "Succeeded" ]
cd 'C:\ALLOOLOO\CM-KG\RAILS\job'
python -X utf8 -I provision_jobs.py create $TAG $CC 2>&1 | grep -v WARNING | tail -3 || { python -c "import time;time.sleep(90)"; python -X utf8 -I provision_jobs.py create $TAG $CC 2>&1 | grep -v WARNING | tail -3; }
G=$(az containerapp job list --query "[?name=='cmkg-$CC-rail'].resourceGroup | [0]" -o tsv)
E=$(az containerapp job start -n cmkg-$CC-rail -g $G --query name -o tsv); echo "run $E"
python -X utf8 -I provision_jobs.py upgrade $TAG   # ENUM-01: no cc list = every roster node + apex 2>&1 | grep -v WARNING | sed 's/ · env changed.*//'
python -X utf8 -I provision_jobs.py digest $TAG 2>&1 | grep -v WARNING | tail -2
O=/c/Users/matth/AppData/Local/Temp/claude/C--bpc-agent/487034dc-d9cf-4486-b1b7-3150b19ff9a0/scratchpad/eco$ECOTAG; rm -rf $O; MSYS_NO_PATHCONV=0 sh /c/ALLOOLOO/CM-KG/ECO/job/build_context.sh $O
az acr build -r allooloocmkg -t eco-refresh:$ECOTAG --no-logs "$S\eco$ECOTAG" -o none 2>&1 | grep -v WARNING | tail -1 || true
for i in $(seq 1 60); do st=$(az acr task list-runs -r allooloocmkg --top 1 --query "[0].status" -o tsv); case "$st" in Running|Queued) sleep 20;; *) break;; esac; done; echo "eco image $ECOTAG $st"
[ "$st" = "Succeeded" ] && (cd 'C:\ALLOOLOO\CM-KG\ECO\job' && python -X utf8 -I provision_eco.py $ECOTAG 2>&1 | grep -v WARNING | tail -1)
for i in $(seq 1 110); do s=$(az containerapp job execution show -n cmkg-$CC-rail -g $G --job-execution-name $E --query "properties.status" -o tsv 2>/dev/null); case "$s" in Succeeded|Failed|Stopped) break;; esac; sleep 30; done
echo "$CC run $E $s"
python -X utf8 -I 'C:\ALLOOLOO\CM-KG\RAILS\job\capacity_snapshot.py' > /dev/null 2>&1 && echo 'capacity snapshot written'   # DIGEST-CAP-01: after every provisioning change
