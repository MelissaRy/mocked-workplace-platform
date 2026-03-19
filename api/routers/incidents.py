from fastapi import APIRouter
import db, cache

router = APIRouter()


@router.get("/summary")
async def summary():
    cached = cache.get("incidents_summary")
    if cached:
        return cached
    async with db.pg_pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
                SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved,
                ROUND(AVG(resolution_days), 1) AS avg_resolution_days
            FROM incidents
        """)
        by_severity = await conn.fetch("""
            SELECT severity, COUNT(*) AS count FROM incidents GROUP BY severity ORDER BY count DESC
        """)
        by_category = await conn.fetch("""
            SELECT category, COUNT(*) AS count FROM incidents GROUP BY category ORDER BY count DESC
        """)

    result = {
        "total":              int(stats["total"]),
        "open":               int(stats["open"] or 0),
        "in_progress":        int(stats["in_progress"] or 0),
        "resolved":           int(stats["resolved"] or 0),
        "avg_resolution_days": float(stats["avg_resolution_days"] or 0),
        "by_severity":        {r["severity"]: r["count"] for r in by_severity},
        "by_category":        [{"category": r["category"], "count": r["count"]} for r in by_category],
    }
    cache.set("incidents_summary", result)
    return result


@router.get("/recent")
async def recent():
    cached = cache.get("incidents_recent")
    if cached:
        return cached
    async with db.pg_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT i.id, i.type, i.category, i.severity, i.status,
                   i.opened_date, e.name AS employee, l.hostname
            FROM incidents i
            JOIN employees e ON i.employee_id = e.id
            JOIN laptops l ON i.laptop_id = l.id
            WHERE i.status IN ('Open', 'In Progress')
            ORDER BY i.opened_date DESC
            LIMIT 20
        """)
    result = {"incidents": [
        {
            "id":          r["id"],
            "type":        r["type"],
            "category":    r["category"],
            "severity":    r["severity"],
            "status":      r["status"],
            "opened_date": str(r["opened_date"]),
            "employee":    r["employee"],
            "hostname":    r["hostname"],
        } for r in rows
    ]}
    cache.set("incidents_recent", result)
    return result


@router.get("/trend")
async def trend():
    cached = cache.get("incidents_trend")
    if cached:
        return cached
    async with db.pg_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT TO_CHAR(opened_date, 'YYYY-MM') AS month, COUNT(*) AS count
            FROM incidents
            WHERE opened_date >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY month
            ORDER BY month
        """)
    result = {
        "labels": [r["month"] for r in rows],
        "counts": [r["count"] for r in rows],
    }
    cache.set("incidents_trend", result)
    return result
