#!/bin/bash
# ORDER-031 — wait for a set of dry-run executions to end, then diff each against the 2026-10-16 record. One read per minute of Azure's own
# execution state (not an external clock; the executions are ours). Usage: bash watch_dryruns.sh cc:region:execution [...]
export AZURE_CONFIG_DIR='C:\ALLOOLOO\.azure' MSYS_NO_PATHCONV=1 PYTHONIOENCODING=utf-8 PYTHONUTF8=1
cd /c/ALLOOLOO/CM-KG/RAILS/job
declare -A done
while :; do
  left=0
  for t in "$@"; do
    IFS=: read cc reg ex <<< "$t"
    [ -n "${done[$cc]}" ] && continue
    st=$(az containerapp job execution show -n cmkg-$cc-rail -g allooloo-cmkg-$reg --job-execution-name $ex --query properties.status -o tsv 2>/dev/null | tr -d '\r')
    if [ -n "$st" ] && [ "$st" != "Running" ] && [ "$st" != "Processing" ]; then done[$cc]=$st; echo "$(date -u +%H:%M) $cc $ex $st"; else left=$((left+1)); fi
  done
  [ $left -eq 0 ] && break
  sleep 60
done
for t in "$@"; do
  IFS=: read cc reg ex <<< "$t"
  echo "===== $cc ($ex ${done[$cc]})"
  python -I dryrun_diff.py $cc 2026-10-16 staging 2>&1 | grep -v WARNING
done
