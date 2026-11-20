FROM python:3.12-slim

# No bytecode writes: the runtime filesystem is read-only in-cluster.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY hr/     ./hr/
COPY mdm/    ./mdm/
COPY itsm/   ./itsm/

# WORKER is set by the Kubernetes Job/CronJob (hr | mdm | itsm)
ENV WORKER=hr

# Matches runAsUser in the Kubernetes manifests, so the pod can enforce
# runAsNonRoot without guessing a uid.
RUN useradd --create-home --uid 10001 appuser
USER 10001

CMD python -m ${WORKER}.ingest
