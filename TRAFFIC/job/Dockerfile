# traffic-run — SITE-04 (2026-10-28): the standing TRAFFIC run (cmkg-traffic-nightly, Allooloo tenant, 02:30 UTC). One rail, the roster of record beside it.
# Build (cloud, no local Docker): sh C:\ALLOOLOO\TRAFFIC\job\build_context.sh <ctx> && az acr build -r allooloocmkg -t traffic-run:<tag> <ctx>
FROM python:3.12-slim
ENV PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 PYTHONUTF8=1 TZ=UTC
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir openpyxl==3.1.5 azure-identity==1.19.0 azure-storage-blob==12.26.0
WORKDIR /app
COPY traffic_nightly.py roster.xlsx /app/
ENV ROSTER_XLSX=/app/roster.xlsx OUT_DIR=/tmp/traffic
CMD ["python", "-X", "utf8", "-I", "traffic_nightly.py"]
