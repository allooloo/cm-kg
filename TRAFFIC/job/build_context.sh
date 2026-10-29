#!/bin/sh
# assemble the traffic-run build context: the rail + the roster of record (renamed roster.xlsx) + the Dockerfile. Usage: sh build_context.sh <out dir>
set -e; OUT="$1"; rm -rf "$OUT"; mkdir -p "$OUT"
cp /c/ALLOOLOO/TRAFFIC/job/Dockerfile "$OUT/"
cp /c/ALLOOLOO/TRAFFIC/rails/traffic_nightly.py "$OUT/"
cp "/c/ALLOOLOO/TRAFFIC/ALLOOLOO_TRAFFIC_zone-roster_v1.3_2026-10-28.xlsx" "$OUT/roster.xlsx"
ls -la "$OUT"
