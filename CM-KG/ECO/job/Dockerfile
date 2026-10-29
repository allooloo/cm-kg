# eco-refresh — ECO-01 RUN (CEO day order 2, 2026-10-23). Weekly Sunday 05:00 UTC in the Allooloo tenant: re-read sources, flag, re-sign, redeploy eco-pages, digest row, ark.
# 0.1.2 (2026-10-24): Node 22 from the official image (wrangler 4.152 refuses Node 20 — the 0.1.1 run's deploy_rc 1); only node + npm are copied, the Python of the base stays.
FROM node:22-bookworm-slim AS node
FROM python:3.12-slim
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
 && apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir cryptography azure-identity azure-storage-blob boto3 python-docx && npm install -g wrangler@4.152.0 && node --version && wrangler --version
WORKDIR /app/CM-KG/ECO
COPY CM-KG/ /app/CM-KG/
CMD ["python", "-X", "utf8", "-I", "refresh_eco.py"]
