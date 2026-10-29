# ARM-BACKFILL.sh — BACKFILL-01 (DAY ORDER 7, 2026-10-25): the CEO's hand, then one rail. Git Bash, from C:\ALLOOLOO\CM-KG\RAILS\job.
# Step 1 (a key — the CEO's hand; CC's session was refused "Secret-Store Writes"): the node-record signing key into the eleven vaults the backfill jobs read,
# by file name (the value is never typed or printed).
export AZURE_CONFIG_DIR='C:\ALLOOLOO\.azure' MSYS_NO_PATHCONV=1
for v in allooloo-cmkg-kv-au allooloo-cmkg-kv-ca allooloo-cmkg-kv-ch allooloo-cmkg-kv-de allooloo-cmkg-kv-fr allooloo-cmkg-kv-jp allooloo-cmkg-kv-kr allooloo-cmkg-kv-nl allooloo-cmkg-kv-sg allooloo-cmkg-kv-uk allooloo-cmkg-kv-us; do
  az keyvault secret set --vault-name $v -n cmr-signing-jwk --file 'C:\ALLOOLOO\AGENT KEYS\cmr-signing-jwk.txt' --query name -o tsv
done
# Step 2 (the rail): one backfill job per armed roster node, 30 14 * * * UTC, image cmkg-sweep:0.35.1 (ky bm je carry no pull of their own: no job).
python -X utf8 -I provision_jobs.py backfill 0.35.1
# Step 3: the capacity snapshot (the digest's capacity block reads it)
python -X utf8 -I capacity_snapshot.py > /dev/null && echo capacity snapshot written
