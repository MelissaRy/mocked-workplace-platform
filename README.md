# Mocked Workplace Data Platform

A end-to-end data platform simulating real enterprise IT systems — built on Kubernetes (kind), PostgreSQL, Neo4j, and FastAPI.

![Infrastructure Diagram](infra-diagram.svg)

---

## What it is

Three mocked data sources ingest into a relational database (PostgreSQL) and a graph database (Neo4j). A FastAPI service sits on top of both, exposing REST endpoints consumed by a live fleet health dashboard.

| Worker | Mimics | Writes to |
|--------|--------|-----------|
| HR | Workday | PostgreSQL |
| MDM | Jamf | PostgreSQL + Neo4j |
| ITSM | ServiceNow | PostgreSQL + Neo4j |

**PostgreSQL** holds the full relational dataset — employees, laptops, incidents, apps, training.
**Neo4j** holds the graph — relationships between employees, laptops, departments, applications and incidents. Used for traversal queries like "which apps are installed on devices with open security incidents, grouped by department?"

---

## Stack

- **Kubernetes** — [kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker) local cluster
- **PostgreSQL** — bitnami/postgresql Helm chart, StatefulSet
- **Neo4j** — neo4j/neo4j Helm chart, community edition, StatefulSet
- **Ingestion workers** — Python (psycopg2 + neo4j driver), containerised, run as Kubernetes Jobs
- **API** — FastAPI + asyncpg + neo4j async driver, Kubernetes Deployment
- **Dashboard** — Jinja2 template + Chart.js, served by FastAPI at `localhost:8000`

---

## Project structure

```
cluster/        kind cluster config (port mappings)
helm/           Helm values (gitignored — contains passwords)
ingestion/      Python ingestion workers (HR, MDM, ITSM)
  shared/       DB connection helpers, schema bootstrap, mock data
  hr/           HR ingestion worker
  mdm/          MDM ingestion worker
  itsm/         ITSM ingestion worker
api/            FastAPI application + dashboard
  routers/      Endpoint modules (overview, fleet, security, incidents, graph)
  templates/    Jinja2 dashboard HTML
k8s/            Kubernetes manifests (ConfigMap, Jobs, Deployment, Services)
```

---

## Dataset (mocked)

| Table | Records |
|-------|---------|
| employees | 1,000 |
| departments | 15 |
| laptops + metrics | 1,000 |
| applications | 24 |
| laptop_applications | 11,002 |
| incidents | 873 |
| employee_training | 7,419 |

Neo4j graph: 6 node types, 5 relationship types.

---

## Phases

- [x] **Phase 1** — kind cluster + PostgreSQL + Neo4j via Helm
- [x] **Phase 2** — Containerised ingestion pipeline (HR → MDM → ITSM)
- [x] **Phase 3** — FastAPI fleet health dashboard
- [ ] **Phase 4** — CI/CD (GitHub Actions: lint → test → build → push → deploy)

---

## Setup

> Credentials are injected via Kubernetes ConfigMap. Copy `k8s/configmap.yaml`, fill in your values, and apply before running the jobs.

```bash
# 1. Create the kind cluster
kind create cluster --config cluster/kind-config.yaml

# 2. Install databases via Helm
helm install postgres bitnami/postgresql --namespace workplace --create-namespace -f helm/postgres-values.yaml
helm install neo4j neo4j/neo4j --namespace workplace -f helm/neo4j-values.yaml

# 3. Apply k8s manifests
kubectl apply -f k8s/

# 4. Build and load ingestion image
docker build -t workplace-ingestion:latest ingestion/
kind load docker-image workplace-ingestion:latest --name workplace-platform

# 5. Run ingestion jobs (in order)
kubectl create job hr-run   --from=cronjob/hr-ingestion   -n workplace  # or apply jobs.yaml
kubectl create job mdm-run  --from=cronjob/mdm-ingestion  -n workplace
kubectl create job itsm-run --from=cronjob/itsm-ingestion -n workplace

# 6. Build and deploy the API
docker build -t workplace-api:latest api/
kind load docker-image workplace-api:latest --name workplace-platform
kubectl apply -f k8s/api-deployment.yaml

# 7. Open the dashboard
open http://localhost:8000
```
