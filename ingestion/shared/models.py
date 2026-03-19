"""
Shared data models and DB connection helpers.
"""

import os
import psycopg2
from psycopg2.extras import execute_values
from neo4j import GraphDatabase

# ── connection ────────────────────────────────────────────────────────────────

PG_DSN     = os.environ["PG_DSN"]
NEO4J_URI  = os.environ["NEO4J_URI"]
NEO4J_USER = os.environ["NEO4J_USER"]
NEO4J_PASS = os.environ["NEO4J_PASS"]

def pg_conn():
    return psycopg2.connect(PG_DSN)

def neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

# ── schema bootstrap ──────────────────────────────────────────────────────────

SCHEMA_SQL = """
-- HR
CREATE TABLE IF NOT EXISTS departments (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL,
    division    VARCHAR(100),
    office      VARCHAR(100),
    head_name   VARCHAR(100),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS employees (
    id              VARCHAR(20) PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(150) UNIQUE NOT NULL,
    title           VARCHAR(150),
    department_id   INT REFERENCES departments(id),
    office          VARCHAR(100),
    hire_date       DATE,
    employee_type   VARCHAR(50),
    seniority       VARCHAR(50),
    status          VARCHAR(20) DEFAULT 'Active',
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- MDM (Device Management)
CREATE TABLE IF NOT EXISTS laptops (
    id              VARCHAR(20) PRIMARY KEY,
    employee_id     VARCHAR(20) REFERENCES employees(id),
    hostname        VARCHAR(100) UNIQUE NOT NULL,
    make            VARCHAR(50),
    model           VARCHAR(100),
    serial          VARCHAR(50) UNIQUE,
    os              VARCHAR(100),
    ram_gb          INT,
    cpu             VARCHAR(100),
    storage_gb      INT,
    assigned_date   DATE,
    warranty_expiry DATE,
    status          VARCHAR(50),
    managed         BOOLEAN DEFAULT TRUE,
    disk_encrypted  BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS laptop_metrics (
    id                  SERIAL PRIMARY KEY,
    laptop_id           VARCHAR(20) REFERENCES laptops(id),
    cpu_usage_pct       INT,
    ram_usage_pct       INT,
    disk_usage_pct      INT,
    battery_health_pct  INT,
    uptime_days         INT,
    os_patches_missing  INT,
    antivirus_status    VARCHAR(50),
    disk_encrypted      BOOLEAN,
    firewall_enabled    BOOLEAN,
    screen_lock_mins    INT,
    last_backup         DATE,
    last_seen           DATE,
    recorded_at         TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS applications (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(150) UNIQUE NOT NULL,
    vendor        VARCHAR(100),
    category      VARCHAR(100),
    license_type  VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS laptop_applications (
    laptop_id         VARCHAR(20) REFERENCES laptops(id),
    application_id    INT REFERENCES applications(id),
    version           VARCHAR(50),
    install_date      DATE,
    auto_update       BOOLEAN,
    license_compliant BOOLEAN,
    PRIMARY KEY (laptop_id, application_id)
);

-- ITSM (Incident Management)
CREATE TABLE IF NOT EXISTS incidents (
    id              VARCHAR(20) PRIMARY KEY,
    laptop_id       VARCHAR(20) REFERENCES laptops(id),
    employee_id     VARCHAR(20) REFERENCES employees(id),
    type            VARCHAR(100),
    category        VARCHAR(100),
    severity        VARCHAR(20),
    status          VARCHAR(50),
    opened_date     DATE,
    resolved_date   DATE,
    resolution_days INT,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS training_courses (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(200) UNIQUE NOT NULL,
    category      VARCHAR(100),
    validity_days INT
);

CREATE TABLE IF NOT EXISTS employee_training (
    employee_id     VARCHAR(20) REFERENCES employees(id),
    course_id       INT REFERENCES training_courses(id),
    completed_date  DATE,
    expiry_date     DATE,
    status          VARCHAR(50),
    score_pct       INT,
    PRIMARY KEY (employee_id, course_id)
);
"""

def bootstrap_schema():
    with pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()
    print("Schema ready.")
