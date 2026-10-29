#!/bin/sh
# assemble the eco-ops build context: the rail, the generator + registry, the SITE-03A lane rails, the GREAT-CULL-02 upload rail with the 148 snapshots of record.
# Never: AGENT KEYS, .azure, backups, .pre files. Usage: sh build_context.sh <out dir>
set -e; OUT="$1"; rm -rf "$OUT"; mkdir -p "$OUT/app/ECO-OPS" "$OUT/app/PROTOCOLS/_canon/registry" "$OUT/app/LANE" "$OUT/app/CULL/snapshots" "$OUT/app/CULL/roll" "$OUT/app/CULL/pages"
cp /c/ALLOOLOO/ECO-OPS/Dockerfile "$OUT/"
cp /c/ALLOOLOO/ECO-OPS/eco_ops.py /c/ALLOOLOO/ECO-OPS/sign_ops.py "$OUT/app/ECO-OPS/"
cp /c/GREENCORE/PROTOCOLS/site03a.py "$OUT/app/PROTOCOLS/"; cp /c/GREENCORE/PROTOCOLS/_canon/registry/estate.json "$OUT/app/PROTOCOLS/_canon/registry/"
cp /c/GREENCORE/AUDITS/SITE-03A-2026-10-28/grep_banned.py /c/GREENCORE/AUDITS/SITE-03A-2026-10-28/verify_site03a.py "$OUT/app/LANE/"
cp /c/GREENCORE/AUDITS/GREAT-CULL-02-2026-10-10/pages_app.py "$OUT/app/CULL/"
grep -E '^app,|^gp-sm,' /c/GREENCORE/AUDITS/GREAT-CULL-02-2026-10-10/AUDIT.csv > "$OUT/app/CULL/AUDIT.csv" || head -1 /c/GREENCORE/AUDITS/GREAT-CULL-02-2026-10-10/AUDIT.csv > "$OUT/app/CULL/AUDIT.csv"
S=/c/GREENCORE/AUDITS/GREAT-CULL-02-2026-10-10/snapshots
# VAULT-DROP-01: every gp-sm host of AUDIT.csv (200: the 148 + the 52 country eco.io hosts), so pages_app.py cuts the same three parts as the laptop
for h in $(python -X utf8 -c "import csv,io;r={x['app']:x for x in csv.DictReader(io.open(r'C:/GREENCORE/AUDITS/GREAT-CULL-02-2026-10-10/AUDIT.csv',encoding='utf-8'))};print(' '.join(sorted(h for h in r['gp-sm']['hostnames'].split() if not h.startswith('www.'))))"); do
  mkdir -p "$OUT/app/CULL/snapshots/$h"; cp -r "$S/$h/." "$OUT/app/CULL/snapshots/$h/"; cp "$S/$h.manifest.json" "$OUT/app/CULL/snapshots/"
done
find "$OUT/app" -name "*.pre*" -delete
echo "context: $(find "$OUT" -type f | wc -l) files, $(du -sh "$OUT" | cut -f1)"
