"""
ITSM Ingestion Worker — simulates a ServiceNow-like incident management system.
Writes incidents to PostgreSQL and syncs to Neo4j.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import timedelta
from shared.models import pg_conn, neo4j_driver
from shared.mock_data import INCIDENT_TYPES, rand_date, rng

N_EMPLOYEES = int(os.getenv("N_EMPLOYEES", "1000"))


def ingest_incidents(cur, n):
    print(f"  Ingesting incidents for {n} employees...")
    for i in range(1, n + 1):
        emp_id = f"USR{i:04d}"
        lid    = f"LT{i:04d}"

        cur.execute("SELECT id FROM laptops WHERE id = %s", (lid,))
        if not cur.fetchone():
            continue

        n_inc = rng.choices([0,1,2,3], weights=[45,30,15,10])[0]
        for j in range(n_inc):
            inc   = rng.choice(INCIDENT_TYPES)
            opened = rand_date(2024, 2025)
            resolved = opened + timedelta(days=rng.randint(1,14)) if rng.random() > 0.3 else None
            status = "Resolved" if resolved else rng.choice(["Open","In Progress"])
            inc_id = f"INC{i:04d}{j}"

            cur.execute("""
                INSERT INTO incidents (id, laptop_id, employee_id, type, category, severity,
                                       status, opened_date, resolved_date, resolution_days)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO NOTHING
            """, (inc_id, lid, emp_id, inc[0], inc[1], inc[2], status,
                  opened, resolved, (resolved - opened).days if resolved else None))


def sync_incidents_to_neo4j(pg_cur):
    print("  Syncing incidents to Neo4j...")
    pg_cur.execute("""
        SELECT id, laptop_id, type, category, severity, status, opened_date
        FROM incidents LIMIT 2000
    """)
    rows = pg_cur.fetchall()

    driver = neo4j_driver()
    with driver.session() as s:
        BATCH = 200
        for i in range(0, len(rows), BATCH):
            chunk = rows[i:i+BATCH]
            s.run("""
                UNWIND $rows AS r
                MATCH (l:Laptop {id:r.lid})
                CREATE (i:Incident {id:r.id})
                SET i.type=r.type, i.category=r.category,
                    i.severity=r.severity, i.status=r.status,
                    i.opened_date=r.opened_date
                CREATE (l)-[:HAD_INCIDENT]->(i)
            """, rows=[{
                "id":r[0],"lid":r[1],"type":r[2],
                "category":r[3],"severity":r[4],
                "status":r[5],"opened_date":str(r[6])
            } for r in chunk])
    driver.close()
    print("  Neo4j incident sync complete.")


def run():
    print("[ITSM] Starting ingestion...")
    with pg_conn() as conn:
        with conn.cursor() as cur:
            ingest_incidents(cur, N_EMPLOYEES)
        conn.commit()
        with conn.cursor() as cur:
            sync_incidents_to_neo4j(cur)
    print("[ITSM] Done.")


if __name__ == "__main__":
    run()
