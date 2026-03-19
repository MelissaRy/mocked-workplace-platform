"""
MDM Ingestion Worker — simulates a Jamf-like device management system.
Writes laptops, metrics and apps to PostgreSQL, then syncs relationships to Neo4j.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from shared.models import pg_conn, neo4j_driver, bootstrap_schema
from shared.mock_data import (
    LAPTOP_CONFIGS, CPU_MAP, APPS, rand_date, weighted_choice, rng
)

N_EMPLOYEES = int(os.getenv("N_EMPLOYEES", "1000"))

DEVICE_STATUSES = ["Active","Active","Active","Active","Pending Refresh","Warranty Expired","In Repair"]

DEPT_APPS = {
    "Engineering":      ["VS Code","Docker Desktop","Jira","Confluence","AWS CLI","Slack","CrowdStrike Falcon"],
    "Data Science":     ["Jupyter Notebook","Tableau Desktop","VS Code","AWS CLI","Slack","CrowdStrike Falcon"],
    "DevOps":           ["Terraform","Docker Desktop","AWS CLI","Datadog Agent","Slack","CrowdStrike Falcon"],
    "Security":         ["CrowdStrike Falcon","Splunk Universal Fwd","AWS CLI","Zscaler Client","1Password","Slack"],
    "IT":               ["ServiceNow","AWS CLI","Terraform","Datadog Agent","Splunk Universal Fwd","Slack"],
    "Design":           ["Figma","Slack","Zoom","Microsoft 365"],
    "Product":          ["Jira","Confluence","Figma","Slack","Zoom"],
    "Finance":          ["Microsoft 365","Power BI Desktop","Workday","Slack"],
    "Legal":            ["Microsoft 365","Slack","Zoom"],
    "HR":               ["Microsoft 365","Workday","Slack","Zoom"],
    "Sales":            ["Salesforce","Slack","Zoom","Microsoft 365"],
    "Marketing":        ["Figma","Slack","Microsoft 365"],
    "Customer Success": ["Salesforce","Slack","Zoom"],
    "Operations":       ["Microsoft 365","Jira","Tableau Desktop","Slack"],
    "Executive":        ["Microsoft 365","Slack","Zoom","Salesforce"],
}
UNIVERSAL_APPS = ["CrowdStrike Falcon","Okta Verify","1Password","Google Chrome","Cisco AnyConnect","Slack"]


def ingest_apps(cur):
    print("  Ingesting application catalog...")
    for name, vendor, category, license_type in APPS:
        cur.execute("""
            INSERT INTO applications (name, vendor, category, license_type)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (name, vendor, category, license_type))


def ingest_laptops(cur, n):
    print(f"  Ingesting {n} laptops...")
    used_serials = set()

    for i in range(1, n + 1):
        emp_id = f"USR{i:04d}"

        cur.execute("SELECT d.name, d.office FROM employees e JOIN departments d ON e.department_id = d.id WHERE e.id = %s", (emp_id,))
        row = cur.fetchone()
        if not row:
            continue
        dept, office = row

        cfg   = rng.choice(LAPTOP_CONFIGS)
        make, model, os_name, rams, storages = cfg
        ram   = rng.choice(rams)
        stor  = rng.choice(storages)
        cpu   = rng.choice(CPU_MAP[make])

        serial = f"SN{rng.randint(100000,999999)}"
        while serial in used_serials:
            serial = f"SN{rng.randint(100000,999999)}"
        used_serials.add(serial)

        assigned = rand_date(2019, 2024)
        warranty = assigned + timedelta(days=365 * 3)
        status   = rng.choice(DEVICE_STATUSES)
        if warranty < date.today():
            status = rng.choices(["Warranty Expired","Pending Refresh","Active"], weights=[50,35,15])[0]

        hostname = f"{dept[:3].lower()}-{emp_id.lower()}-{rng.randint(1,99):02d}"
        lid      = f"LT{i:04d}"

        cur.execute("""
            INSERT INTO laptops (id, employee_id, hostname, make, model, serial, os, ram_gb, cpu, storage_gb,
                                 assigned_date, warranty_expiry, status, managed, disk_encrypted)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO UPDATE SET status=EXCLUDED.status, updated_at=NOW()
        """, (lid, emp_id, hostname, make, model, serial, os_name, ram, cpu, stor,
              assigned, warranty, status, True, rng.choices([True,False], weights=[88,12])[0]))

        # metrics
        old   = status in ("Warranty Expired","Pending Refresh","Decommissioned")
        risky = old or rng.random() < 0.12
        cur.execute("""
            INSERT INTO laptop_metrics (laptop_id, cpu_usage_pct, ram_usage_pct, disk_usage_pct,
                battery_health_pct, uptime_days, os_patches_missing, antivirus_status,
                disk_encrypted, firewall_enabled, screen_lock_mins, last_backup, last_seen)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            lid,
            rng.randint(5,95),
            rng.randint(25,98) if old else rng.randint(10,82),
            rng.randint(65,97) if old else rng.randint(10,75),
            rng.randint(20,60) if old else rng.randint(70,100),
            rng.randint(30,90) if old else rng.randint(0,21),
            rng.randint(5,25)  if risky else rng.randint(0,2),
            rng.choices(["OK","OUTDATED","WARNING","NOT INSTALLED"], weights=[65,18,12,5])[0] if risky else "OK",
            not risky or rng.random() > 0.35,
            not risky or rng.random() > 0.3,
            rng.choice([5,10,15,30,0]),
            date.today() - timedelta(days=rng.randint(7,60) if risky else rng.randint(0,3)),
            date.today() - timedelta(days=rng.randint(5,30) if risky else rng.randint(0,2)),
        ))

        # app installs
        required = set(UNIVERSAL_APPS + DEPT_APPS.get(dept, []))
        extra    = set(rng.sample([a[0] for a in APPS], k=rng.randint(1, 4)))
        for app_name in required | extra:
            cur.execute("SELECT id FROM applications WHERE name = %s", (app_name,))
            app_row = cur.fetchone()
            if not app_row:
                continue
            cur.execute("""
                INSERT INTO laptop_applications (laptop_id, application_id, version, install_date, auto_update, license_compliant)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (laptop_id, application_id) DO NOTHING
            """, (lid, app_row[0],
                  f"{rng.randint(1,20)}.{rng.randint(0,9)}.{rng.randint(0,9)}",
                  rand_date(2020, 2025),
                  rng.choices([True,False], weights=[68,32])[0],
                  rng.choices([True,False], weights=[94,6])[0]))


def sync_to_neo4j(pg_cur):
    print("  Syncing relationships to Neo4j...")
    driver = neo4j_driver()
    with driver.session() as s:
        s.run("MATCH (n) DETACH DELETE n")

        # departments
        pg_cur.execute("SELECT name, division, office FROM departments")
        depts = pg_cur.fetchall()
        s.run("UNWIND $rows AS r MERGE (d:Department {name:r.name}) SET d.division=r.division, d.office=r.office",
              rows=[{"name": r[0], "division": r[1], "office": r[2]} for r in depts])

        # offices
        offices = list(set(r[2] for r in depts))
        s.run("UNWIND $rows AS r MERGE (o:Office {name:r})", rows=offices)
        s.run("UNWIND $rows AS r MATCH (d:Department {office:r.name}) MATCH (o:Office {name:r.name}) MERGE (d)-[:BASED_IN]->(o)",
              rows=[{"name": o} for o in offices])

        # employees
        pg_cur.execute("SELECT e.id, e.name, e.email, e.title, e.seniority, d.name FROM employees e JOIN departments d ON e.department_id=d.id LIMIT 1000")
        emps = pg_cur.fetchall()
        BATCH = 100
        for i in range(0, len(emps), BATCH):
            chunk = emps[i:i+BATCH]
            s.run("""
                UNWIND $rows AS r
                MERGE (e:Employee {id:r.id})
                SET e.name=r.name, e.email=r.email, e.title=r.title, e.seniority=r.seniority
                WITH e, r
                MATCH (d:Department {name:r.dept})
                MERGE (e)-[:WORKS_IN]->(d)
            """, rows=[{"id":r[0],"name":r[1],"email":r[2],"title":r[3],"seniority":r[4],"dept":r[5]} for r in chunk])

        # laptops
        pg_cur.execute("SELECT l.id, l.hostname, l.make, l.model, l.os, l.status, l.employee_id FROM laptops l LIMIT 1000")
        laps = pg_cur.fetchall()
        for i in range(0, len(laps), BATCH):
            chunk = laps[i:i+BATCH]
            s.run("""
                UNWIND $rows AS r
                MERGE (l:Laptop {id:r.id})
                SET l.hostname=r.hostname, l.make=r.make, l.model=r.model, l.os=r.os, l.status=r.status
                WITH l, r
                MATCH (e:Employee {id:r.emp})
                MERGE (e)-[:ASSIGNED_TO]->(l)
            """, rows=[{"id":r[0],"hostname":r[1],"make":r[2],"model":r[3],"os":r[4],"status":r[5],"emp":r[6]} for r in chunk])

        # apps
        pg_cur.execute("""
            SELECT DISTINCT a.name, a.category
            FROM laptop_applications la JOIN applications a ON la.application_id=a.id
        """)
        apps = pg_cur.fetchall()
        s.run("UNWIND $rows AS r MERGE (a:Application {name:r.name}) SET a.category=r.category",
              rows=[{"name":r[0],"category":r[1]} for r in apps])

        pg_cur.execute("""
            SELECT l.id, a.name FROM laptop_applications la
            JOIN laptops l ON la.laptop_id=l.id
            JOIN applications a ON la.application_id=a.id
            LIMIT 5000
        """)
        installs = pg_cur.fetchall()
        for i in range(0, len(installs), 500):
            chunk = installs[i:i+500]
            s.run("""
                UNWIND $rows AS r
                MATCH (l:Laptop {id:r.lid})
                MATCH (a:Application {name:r.app})
                MERGE (l)-[:HAS_INSTALLED]->(a)
            """, rows=[{"lid":r[0],"app":r[1]} for r in chunk])

    driver.close()
    print("  Neo4j sync complete.")


def run():
    print("[MDM] Starting ingestion...")
    with pg_conn() as conn:
        with conn.cursor() as cur:
            ingest_apps(cur)
            ingest_laptops(cur, N_EMPLOYEES)
        conn.commit()
        with conn.cursor() as cur:
            sync_to_neo4j(cur)
    print("[MDM] Done.")


if __name__ == "__main__":
    run()
