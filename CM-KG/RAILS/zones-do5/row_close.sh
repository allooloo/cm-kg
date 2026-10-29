#!/bin/sh
# row_close.sh — NODE-ROW-01…09 (DAY ORDER 5, 2026-10-24): one ROW node from its harvested pond to a live door on its own zone, on the NODE-EU steps (eu_close.sh):
#   1 door data: load_nodes.py <cc>; the halt reader (RAILS\row-sources\<cc>\halt.py names its own read_by) into RAILS\halts\halt_<cc>.py; enrich_node.py <cc>
#   2 region: provision_region.py <cc> <store region> storage | upload | app 0.16.0 (door + job in the ENV_HOST environment); NODE_EXAMPLE on the door
#   3 zone door: row_door.py <cc> — mcp./agent.<cc>-cm-kg.ai bound with the zone's Origin CA certificate, gate route
#   4 apex: apex_join.py (no EU_DOOR: the own-zone default; no HOME for ky bm je); build_index.py; the apex deployed
#   5 ECO: example on the public door; build_eco.py 2026-10-23,2026-10-24; eco-pages deployed (NODE LIVE from live.json)
#   6 pages: row-nodes.json (residency), build_do5_data.py, estate-pages deployed (the issuer page and the node surface flip to NODE LIVE)
# The image, the job and the nightly cron follow in eu_job.sh. Usage: sh row_close.sh <cc> <store region> <MIC/ISIN example> <example ISIN> <example name>
set -e
CC="$1"; REGION="$2"; EX="$3"; EXISIN="$4"; EXNAME="$5"; R=/c/ALLOOLOO/CM-KG; Z=$R/RAILS/zones-do5
export AZURE_CONFIG_DIR="C:/ALLOOLOO/.azure" PYTHONUTF8=1 PYTHONIOENCODING=utf-8
cd $R/RAILS/door && python -X utf8 load_nodes.py $CC 2>&1 | tail -2
printf '%s
' "# halt_$CC.py — NODE-ROW (DAY ORDER 5): shim; the reader lives with its helpers in RAILS\row-sources\$CC\halt.py (loaded from there, in the job image too)" "import os, sys, importlib.util" "_d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'row-sources', '$CC'); sys.path.insert(0, _d)" "_s = importlib.util.spec_from_file_location('row_${CC}_halt', os.path.join(_d, 'halt.py')); _m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)" "fetch = _m.fetch" > $R/RAILS/halts/halt_$CC.py
python -X utf8 -I enrich_node.py $CC 2>&1 | tail -2
cd /c/ALLOOLOO/AZURE && for s in storage upload; do python -X utf8 provision_region.py $CC $REGION $s 2>&1 | tail -2; done
python -X utf8 provision_region.py $CC $REGION app 0.16.0 2>&1 | tail -2
export MSYS_NO_PATHCONV=1
G=$(az containerapp list --query "[?name=='cmkg-door-$CC'].resourceGroup | [0]" -o tsv)
FQDN=$(az containerapp show -n cmkg-door-$CC -g $G --query properties.configuration.ingress.fqdn -o tsv)
az containerapp update -n cmkg-door-$CC -g $G --set-env-vars NODE_EXAMPLE=$EX --query "properties.latestRevisionName" -o tsv 2>&1 | tail -1
unset MSYS_NO_PATHCONV
cd $Z && python -X utf8 -I row_door.py $CC
cd $R/RAILS/eu-node && python -X utf8 -I apex_join.py $CC $REGION $FQDN
python -X utf8 -I $R/RAILS/eu-node/nodes_region.py   # DAY ORDER 5: region on the roster entry, read from Azure
cd $R/DOOR/apex && node -e "import('./index.js').then(()=>console.log('apex module ok'))" && python -X utf8 build_index.py 2>&1 | tail -1
export CLOUDFLARE_API_TOKEN="$(head -1 '/c/ALLOOLOO/AGENT KEYS/cloudflare.txt' | tr -d '\r\n')" CLOUDFLARE_ACCOUNT_ID=dd2832b36f171b815f84c8487aada36b WRANGLER_SEND_METRICS=false
npx --yes wrangler@4 deploy 2>&1 | grep -E "Version ID|ERROR" | sed 's/^/apex /'
cd $R/ECO && python -I -X utf8 -c "
import json; p=r'C:\ALLOOLOO\CM-KG\ECO\examples.json'; e=json.load(open(p,encoding='utf-8'))
e['$CC']={'isin':'$EXISIN','name':'$EXNAME','ticker':'$EXISIN','record_url':'https://mcp.$CC-cm-kg.ai/record/$EX','isin_on_node':True}
json.dump(e,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1); print('eco example', '$CC')"
python -X utf8 -I build_eco.py 2026-10-23,2026-10-24 2>&1 | tail -1
npx --yes wrangler@4 deploy 2>&1 | grep -E "Version ID|ERROR" | sed 's/^/eco-pages /'
cd $Z && python -I -X utf8 -c "
import json,os; p='row-nodes.json'; d=json.load(open(p)) if os.path.exists(p) else {}; plan=json.load(open('row-nodes-plan.json'))['$CC']
d['$CC']={'store_region':plan['store_region'],'door_region':plan['door_region'],'door':'https://mcp.$CC-cm-kg.ai/mcp','fqdn':'$FQDN'}; json.dump(d,open(p,'w'),indent=1); print('row-nodes', sorted(d))"
python -X utf8 -I build_do5_data.py && cd $R/ESTATE && npx --yes wrangler@4 deploy 2>&1 | grep -E "Version ID|ERROR" | sed 's/^/estate-pages /'
echo "$CC door https://mcp.$CC-cm-kg.ai (origin https://$FQDN)" > $R/RAILS/eu-node/door-$CC.txt
