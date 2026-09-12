# ORDER-018 — the United States rail as a Container Apps job in East US: EDGAR pull with a declared User-Agent, Width 0 -> Width 1 -> Fill -> door render, written to the East US pond.
FROM python:3.12-slim
WORKDIR /job
RUN pip install --no-cache-dir requests==2.32.3 openpyxl==3.1.5 azure-storage-blob==12.26.0
COPY us_pipeline.py ./
ENV PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
CMD ["python", "us_pipeline.py"]
