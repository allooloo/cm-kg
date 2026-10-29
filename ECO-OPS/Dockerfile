# eco-ops — ECO-OPS-01 (2026-10-28): the nightly rebuild of the SM-ECO-10060 set (cmkg-eco-ops, Allooloo tenant, 03:00 UTC).
# Python for the generator, signer and verifier; Node 22 + wrangler 4 for the Pages upload (the eco-refresh image pattern).
# Build (cloud): sh C:\ALLOOLOO\ECO-OPS\build_context.sh <ctx> && az acr build -r allooloocmkg -t eco-ops:<tag> <ctx>
FROM node:22-bookworm-slim AS node
FROM python:3.12-slim
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
 && apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir httpx cryptography azure-identity azure-storage-blob boto3 && npm install -g wrangler@4.152.0 && node --version && wrangler --version
ENV PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 PYTHONUTF8=1 TZ=UTC CI=1 WRANGLER_SEND_METRICS=false \
    SITE03A_SNAP=/app/CULL/snapshots SITE03A_LANE=/app/LANE SITE03A_REGISTRY=/app/PROTOCOLS/_canon/registry/estate.json CULL_ROOT=/app/CULL PROTOCOLS_DIR=/app/PROTOCOLS
WORKDIR /app/ECO-OPS
COPY app/ /app/
CMD ["python", "-X", "utf8", "eco_ops.py"]
