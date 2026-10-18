# ORDER-031 (2026-10-17) — one image for the eleven in-country sweep jobs and the apex job. Built from the laptop rails as they stand
# (CM-KG\RAILS, AZURE\provision_region.py, CM-KG\DOOR\apex, CM-KG\ESTATE, the numbers-log boot file); paths and secrets are the only change:
# the sitecustomize shim translates C:\ALLOOLOO paths to /job/ALLOOLOO and serves AGENT KEYS reads from the vault-fed environment.
# Node id is the only parameter (NODE_CC); the apex job runs job_apex.py from the same image.
# Build (cloud, no local Docker): python CM-KG\RAILS\job\build_context.py && az acr build -r allooloocmkg -t cmkg-sweep:<tag> -f Dockerfile <context>
FROM python:3.12-slim-bookworm
ENV DEBIAN_FRONTEND=noninteractive PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 \
    CMKG_ROOT=/job/ALLOOLOO CMKG_ROOT_WIN='C:\ALLOOLOO' TZ=UTC CI=1 WRANGLER_SEND_METRICS=false
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gnupg git apt-transport-https \
 && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg \
 && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/microsoft-prod.list \
 && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/azure-cli/ bookworm main" > /etc/apt/sources.list.d/azure-cli.list \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get update && apt-get install -y --no-install-recommends powershell azure-cli nodejs \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir requests==2.32.3 openpyxl==3.1.5 azure-storage-blob==12.26.0 azure-identity==1.19.0 pypdf==5.1.0 boto3==1.35.99 \
 && npm install -g wrangler@4
COPY shim/sitecustomize.py /usr/local/lib/python3.12/site-packages/sitecustomize.py
COPY shim/python /opt/shim/bin/python
RUN chmod 755 /opt/shim/bin/python && ln -s /opt/shim/bin/python /opt/shim/bin/python3
ENV PATH=/opt/shim/bin:$PATH
COPY ALLOOLOO/ /job/ALLOOLOO/
WORKDIR /job/ALLOOLOO/CM-KG/RAILS/job
ENTRYPOINT ["/usr/local/bin/python3", "/job/ALLOOLOO/CM-KG/RAILS/job/job_node.py"]
