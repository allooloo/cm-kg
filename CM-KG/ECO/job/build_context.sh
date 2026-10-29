#!/bin/sh
# assemble the eco-refresh build context: the ECO product folder (no logs, no pond) + the hunt of record. Usage: sh build_context.sh <out dir>
set -e; OUT="$1"; mkdir -p "$OUT/CM-KG/ECO/worker" "$OUT/CM-KG/ECO/data" "$OUT/CM-KG/REFERENCE/ECO"
cp /c/ALLOOLOO/CM-KG/ECO/job/Dockerfile "$OUT/"
cp /c/ALLOOLOO/CM-KG/ECO/build_specs.py /c/ALLOOLOO/CM-KG/ECO/build_eco.py /c/ALLOOLOO/CM-KG/ECO/refresh_eco.py /c/ALLOOLOO/CM-KG/ECO/examples.json /c/ALLOOLOO/CM-KG/ECO/roster.py /c/ALLOOLOO/CM-KG/ECO/wrangler.toml "$OUT/CM-KG/ECO/"
cp /c/ALLOOLOO/CM-KG/ECO/worker/index.js /c/ALLOOLOO/CM-KG/ECO/worker/data.js /c/ALLOOLOO/CM-KG/ECO/worker/rco.js /c/ALLOOLOO/CM-KG/ECO/worker/x402gate.js /c/ALLOOLOO/CM-KG/ECO/worker/package.json "$OUT/CM-KG/ECO/worker/"   # RCO-A-01 + X402-A-01: the receipt and x402 modules ride with the Worker
cp /c/ALLOOLOO/CM-KG/ECO/data/eco-*.json "$OUT/CM-KG/ECO/data/"
cp -r /c/ALLOOLOO/CM-KG/REFERENCE/ECO/hunt-* "$OUT/CM-KG/REFERENCE/ECO/"
mkdir -p "$OUT/CM-KG/RAILS/eu-node" && cp /c/ALLOOLOO/CM-KG/RAILS/eu-node/live.json "$OUT/CM-KG/RAILS/eu-node/"; mkdir -p "$OUT/CM-KG/DOOR/apex/static" "$OUT/CM-KG/ECO" && cp /c/ALLOOLOO/CM-KG/DOOR/apex/static/nodes.json "$OUT/CM-KG/DOOR/apex/static/"   # ENUM-01: the roster file beside   # NODE-EU (2026-10-24): build_eco.py reads the live European nodes from here
for d in eu-sources row-sources; do for r in /c/ALLOOLOO/CM-KG/RAILS/$d/*/README.md; do c=$(basename $(dirname $r)); mkdir -p "$OUT/CM-KG/RAILS/$d/$c"; cp "$r" "$OUT/CM-KG/RAILS/$d/$c/"; done; done   # MARKET-SPECS-01: the stated limits each spec quotes
