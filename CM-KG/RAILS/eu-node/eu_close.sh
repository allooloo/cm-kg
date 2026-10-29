#!/bin/sh
# eu_close.sh — NODE-EU-02…14 (DAY ORDER 4, 2026-10-24): one European node from its harvested pond to a live door, on the Italy (NODE-EU-01) steps.
# Run after `python -X utf8 eu_node.py <cc>` has built the node's pond. Usage: sh eu_close.sh <cc> <region> <MIC/ISIN example> <example ISIN> <example name>
#   1 door data: load_nodes.py <cc>; the halt reader into RAILS\halts\halt_<cc>.py (with its read-by label of record); enrich_node.py <cc>
#   2 region: provision_region.py <cc> <region> storage | upload | app 0.14.0; NODE_EXAMPLE on the door
#   3 apex: apex_join.py <cc> <region> <fqdn>; build_index.py; the apex Worker deployed
#   4 ECO: examples.json gains the node's example; build_eco.py 2026-10-24; eco-pages deployed (the page flips to NODE LIVE from live.json)
# The image, the job and the nightly cron follow in eu_job.sh (the image carries the new live.json and apex copy). Nothing deleted; .pre copies beside.
set -e
CC="$1"; REGION="$2"; EX="$3"; EXISIN="$4"; EXNAME="$5"; R=/c/ALLOOLOO/CM-KG
export AZURE_CONFIG_DIR="C:/ALLOOLOO/.azure" PYTHONUTF8=1 PYTHONIOENCODING=utf-8
label() { case "$1" in
  es) echo "CNMV regulated information (trading suspensions and lifts; BME Growth notices)";;
  se) echo "Nasdaq Stockholm and First North Sweden exchange notices (suspensions, halts, lifts)";;
  dk) echo "Nasdaq Copenhagen and First North Denmark exchange notices (suspensions, halts, lifts)";;
  fi) echo "Nasdaq Helsinki and First North Finland exchange notices (suspensions, halts, lifts)";;
  no) echo "Euronext live - Suspended instruments (current), Oslo MICs";;
  be) echo "Euronext live - Suspended instruments (current), Brussels MICs (XBRU, ALXB)";;
  ie) echo "Euronext live - Suspended instruments (current), Dublin MICs (XMSM, XESM)";;
  gr) echo "Euronext Athens market notices (trading suspensions and resumptions)";;
  cz) echo "Prague Stock Exchange notices (PSE news API, suspension items)";;
  *) echo "";; esac; }
cd $R/RAILS/door && python -X utf8 load_nodes.py $CC 2>&1 | tail -2
cp $R/RAILS/eu-sources/$CC/halt.py $R/RAILS/halts/halt_$CC.py
L="$(label $CC)"; if [ -n "$L" ]; then printf '\n# DAY ORDER 4: the read-by label of record (the node'"'"'s halt flag names its source, not a file)\n_fetch_src = fetch\ndef fetch():\n    h = _fetch_src(); h["read_by"] = "%s"; return h\n' "$L" >> $R/RAILS/halts/halt_$CC.py; fi
python -X utf8 -I enrich_node.py $CC 2>&1 | tail -2
cd /c/ALLOOLOO/AZURE && for s in storage upload; do python -X utf8 provision_region.py $CC $REGION $s 2>&1 | tail -2; done
python -X utf8 provision_region.py $CC $REGION app 0.14.0 2>&1 | tail -2
export MSYS_NO_PATHCONV=1
FQDN=$(az containerapp show -n cmkg-door-$CC -g allooloo-cmkg-$REGION --query properties.configuration.ingress.fqdn -o tsv)
az containerapp update -n cmkg-door-$CC -g allooloo-cmkg-$REGION --set-env-vars NODE_EXAMPLE=$EX --query "properties.latestRevisionName" -o tsv 2>&1 | tail -1
unset MSYS_NO_PATHCONV
echo "door https://$FQDN"
cd $R/RAILS/eu-node && python -X utf8 -I apex_join.py $CC $REGION $FQDN
python -X utf8 -I $R/RAILS/eu-node/nodes_region.py   # DAY ORDER 5: region on the roster entry, read from Azure
cd $R/DOOR/apex && node -e "import('./index.js').then(()=>console.log('apex module ok'))" && python -X utf8 build_index.py 2>&1 | tail -1
export CLOUDFLARE_API_TOKEN="$(head -1 '/c/ALLOOLOO/AGENT KEYS/cloudflare.txt' | tr -d '\r\n')" CLOUDFLARE_ACCOUNT_ID=dd2832b36f171b815f84c8487aada36b WRANGLER_SEND_METRICS=false
npx --yes wrangler@4 deploy 2>&1 | grep -E "Version ID|ERROR" | sed 's/^/apex /'
cd $R/ECO && python -I -X utf8 -c "
import json; p=r'C:\ALLOOLOO\CM-KG\ECO\examples.json'; e=json.load(open(p,encoding='utf-8'))
e['$CC']={'isin':'$EXISIN','name':'$EXNAME','ticker':'$EXISIN','record_url':'https://$FQDN/record/$EX','isin_on_node':True}
json.dump(e,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1); print('eco example', '$CC')"
python -X utf8 -I build_eco.py 2026-10-24 2>&1 | tail -1
npx --yes wrangler@4 deploy 2>&1 | grep -E "Version ID|ERROR" | sed 's/^/eco-pages /'
echo "$CC door https://$FQDN" > $R/RAILS/eu-node/door-$CC.txt
