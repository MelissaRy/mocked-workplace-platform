"""
HR Ingestion Worker — simulates a Workday-like HR system.
Writes employees and departments to PostgreSQL.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import random
from shared.models import pg_conn, bootstrap_schema
from shared.mock_data import (
    DEPARTMENTS, TITLES_BY_DEPT, FIRST_NAMES, LAST_NAMES,
    TRAINING_COURSES, rand_date, rng
)

N_EMPLOYEES = int(os.getenv("N_EMPLOYEES", "1000"))


def ingest_departments(cur):
    print("  Ingesting departments...")
    for name, division, office in DEPARTMENTS:
        cur.execute("""
            INSERT INTO departments (name, division, office)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET division=EXCLUDED.division, office=EXCLUDED.office
        """, (name, division, office))


def ingest_training_courses(cur):
    print("  Ingesting training courses...")
    for name, category, validity in TRAINING_COURSES:
        cur.execute("""
            INSERT INTO training_courses (name, category, validity_days)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (name, category, validity))


def ingest_employees(cur, n):
    print(f"  Ingesting {n} employees...")
    used_names  = set()
    used_emails = set()

    dept_names   = [d[0] for d in DEPARTMENTS]
    dept_weights = [90,60,45,25,30,30,50,40,20,35,70,45,50,40,10]

    for i in range(1, n + 1):
        dept = rng.choices(dept_names, weights=dept_weights, k=1)[0]
        dept_row = next(d for d in DEPARTMENTS if d[0] == dept)
        title    = rng.choice(TITLES_BY_DEPT[dept])
        seniority = (
            "Senior" if any(x in title for x in ["Senior","Staff","Principal","Lead","Manager","Director","VP","Head","Chief","CTO","CEO","COO","CFO","CIO","CISO"])
            else "Junior" if any(x in title for x in ["Junior","Associate","Coordinator","SDR"])
            else "Mid"
        )

        for _ in range(500):
            name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
            if name not in used_names:
                used_names.add(name)
                break

        first, last = name.split()[0].lower(), name.split()[-1].lower()
        email = f"{first}.{last}@corp.local"
        suffix = 1
        base_email = email
        while email in used_emails:
            email = f"{first}.{last}{suffix}@corp.local"
            suffix += 1
        used_emails.add(email)

        emp_type = rng.choices(["Full-time","Contractor","Part-time"], weights=[80,15,5])[0]
        hire_date = rand_date(2015, 2024)

        cur.execute("""
            SELECT id FROM departments WHERE name = %s
        """, (dept,))
        dept_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO employees (id, name, email, title, department_id, office, hire_date, employee_type, seniority)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name=EXCLUDED.name, title=EXCLUDED.title,
                updated_at=NOW()
        """, (f"USR{i:04d}", name, email, title, dept_id, dept_row[2], hire_date, emp_type, seniority))

    return n


def ingest_employee_training(cur, n_employees):
    print("  Ingesting training completions...")
    from datetime import timedelta, date

    mandatory = [
        "Security Awareness Training", "Anti-Harassment & Workplace Ethics",
        "Acceptable Use Policy", "Code of Conduct", "GDPR & Data Privacy",
    ]

    for i in range(1, n_employees + 1):
        emp_id = f"USR{i:04d}"
        extras = rng.sample([c[0] for c in TRAINING_COURSES if c[0] not in mandatory], k=rng.randint(1, 4))
        for course_name in mandatory + extras:
            course = next(c for c in TRAINING_COURSES if c[0] == course_name)
            cur.execute("SELECT id FROM training_courses WHERE name = %s", (course_name,))
            row = cur.fetchone()
            if not row:
                continue
            course_id = row[0]
            completed = rand_date(2021, 2025)
            validity  = course[2]
            if validity:
                expiry = completed + timedelta(days=validity)
                today  = date.today()
                status = "Expired" if expiry < today else "Expiring Soon" if (expiry - today).days < 30 else "Current"
            else:
                expiry, status = None, "Completed"

            cur.execute("""
                INSERT INTO employee_training (employee_id, course_id, completed_date, expiry_date, status, score_pct)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (employee_id, course_id) DO NOTHING
            """, (emp_id, course_id, completed, expiry, status, rng.randint(68, 100)))


def run():
    print("[HR] Starting ingestion...")
    bootstrap_schema()
    with pg_conn() as conn:
        with conn.cursor() as cur:
            ingest_departments(cur)
            ingest_training_courses(cur)
            n = ingest_employees(cur, N_EMPLOYEES)
            ingest_employee_training(cur, n)
        conn.commit()
    print(f"[HR] Done — {N_EMPLOYEES} employees loaded.")


if __name__ == "__main__":
    run()
