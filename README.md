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
k8s/            Kubernetes manifests (ConfigMap, Secret template, Jobs, Deployment, Services)
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

### Configuration and secrets

Configuration is split by sensitivity:

| Where | Holds | Committed |
|---|---|---|
| `k8s/configmap.yaml` | Non-sensitive settings (Neo4j URI, user, record counts) | Yes |
| `platform-secrets` Secret | `PG_DSN`, `NEO4J_PASS` | **No** — created at deploy time |
| `helm/*-values.yaml` | Database passwords for the Helm installs | **No** — gitignored |

ConfigMaps are stored unencrypted in etcd and readable by anything with
namespace read access, so no credential belongs in one. Create the Secret
imperatively, so the values never land in a file:

```bash
kubectl create secret generic platform-secrets \
  --namespace workplace \
  --from-literal=PG_DSN='postgresql://USER:PASSWORD@postgres-postgresql.workplace.svc.cluster.local:5432/workplace_db' \
  --from-literal=NEO4J_PASS='YOUR_NEO4J_PASSWORD'
```

`k8s/secret.example.yaml` documents the shape. A Kubernetes Secret is
base64-encoded rather than encrypted — on a real cluster this should be backed
by encryption-at-rest and an external manager (External Secrets Operator,
Vault, or a cloud KMS-backed store). For a local kind cluster, keeping the
values out of version control is the honest minimum.

Workloads run hardened: non-root (uid 10001), read-only root filesystem with an
explicit `/tmp` scratch mount, all Linux capabilities dropped, no privilege
escalation, and no service-account token mounted.

```bash
# 1. Create the kind cluster
kind create cluster --config cluster/kind-config.yaml

# 2. Install databases via Helm
helm install postgres bitnami/postgresql --namespace workplace --create-namespace -f helm/postgres-values.yaml
helm install neo4j neo4j/neo4j --namespace workplace -f helm/neo4j-values.yaml

# 3. Create the credentials Secret (see "Configuration and secrets" above)
kubectl create namespace workplace --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic platform-secrets --namespace workplace \
  --from-literal=PG_DSN='postgresql://USER:PASSWORD@postgres-postgresql.workplace.svc.cluster.local:5432/workplace_db' \
  --from-literal=NEO4J_PASS='YOUR_NEO4J_PASSWORD'

# 4. Apply k8s manifests (secret.example.yaml is a template — not applied)
kubectl apply -f k8s/configmap.yaml -f k8s/jobs.yaml -f k8s/neo4j-nodeport.yaml

# 5. Build and load ingestion image
docker build -t workplace-ingestion:latest ingestion/
kind load docker-image workplace-ingestion:latest --name workplace-platform

# 6. Run ingestion jobs (in order)
kubectl create job hr-run   --from=cronjob/hr-ingestion   -n workplace  # or apply jobs.yaml
kubectl create job mdm-run  --from=cronjob/mdm-ingestion  -n workplace
kubectl create job itsm-run --from=cronjob/itsm-ingestion -n workplace

# 7. Build and deploy the API
docker build -t workplace-api:latest api/
kind load docker-image workplace-api:latest --name workplace-platform
kubectl apply -f k8s/api-deployment.yaml

# 8. Open the dashboard
open http://localhost:8000
```
