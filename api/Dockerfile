FROM python:3.12-slim

# No bytecode writes: the runtime filesystem is read-only in-cluster.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Matches runAsUser in the Kubernetes manifests, so the pod can enforce
# runAsNonRoot without guessing a uid.
RUN useradd --create-home --uid 10001 appuser
USER 10001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
