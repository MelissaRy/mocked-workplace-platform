FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY hr/     ./hr/
COPY mdm/    ./mdm/
COPY itsm/   ./itsm/

# WORKER is set by the Kubernetes Job/CronJob (hr | mdm | itsm)
ENV WORKER=hr

CMD python -m ${WORKER}.ingest
