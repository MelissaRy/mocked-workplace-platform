from fastapi import APIRouter
import db, cache

router = APIRouter()


@router.get("/risk-summary")
async def risk_summary():
    cached = cache.get("security_risk")
    if cached:
        return cached
    async with db.pg_pool.acquire() as conn:
        tiers = await conn.fetch("""
            WITH scored AS (
                SELECT
                    l.id AS laptop_id,
                    l.hostname,
                    e.name AS employee,
                    (
                        CASE WHEN m.os_patches_missing >= 5 THEN 2 ELSE 0 END +
                        CASE WHEN m.antivirus_status != 'OK' THEN 2 ELSE 0 END +
                        CASE WHEN NOT m.disk_encrypted THEN 3 ELSE 0 END +
                        CASE WHEN NOT m.firewall_enabled THEN 2 ELSE 0 END +
                        CASE WHEN m.battery_health_pct < 40 THEN 1 ELSE 0 END +
                        CASE WHEN m.uptime_days > 30 THEN 1 ELSE 0 END
                    ) AS score
                FROM laptop_metrics m
                JOIN laptops l ON m.laptop_id = l.id
                JOIN employees e ON l.employee_id = e.id
            )
            SELECT
                laptop_id, hostname, employee, score,
                CASE WHEN score = 0 THEN 'healthy'
                     WHEN score <= 2 THEN 'low'
                     WHEN score <= 4 THEN 'medium'
                     ELSE 'high' END AS tier
            FROM scored
            ORDER BY score DESC
        """)

    tier_counts = {"healthy": 0, "low": 0, "medium": 0, "high": 0}
    critical_devices = []
    for r in tiers:
        tier_counts[r["tier"]] += 1
        if len(critical_devices) < 10:
            critical_devices.append({
                "laptop_id": r["laptop_id"],
                "hostname":  r["hostname"],
                "employee":  r["employee"],
                "score":     r["score"],
                "tier":      r["tier"],
            })

    result = {**tier_counts, "critical_devices": critical_devices}
    cache.set("security_risk", result)
    return result


@router.get("/compliance")
async def compliance():
    cached = cache.get("security_compliance")
    if cached:
        return cached
    async with db.pg_pool.acquire() as conn:
        totals = await conn.fetchrow("""
            SELECT
                SUM(CASE WHEN status = 'Current' THEN 1 ELSE 0 END) AS current,
                SUM(CASE WHEN status = 'Expiring Soon' THEN 1 ELSE 0 END) AS expiring_soon,
                SUM(CASE WHEN status = 'Expired' THEN 1 ELSE 0 END) AS expired,
                COUNT(*) AS total
            FROM employee_training
        """)
        worst = await conn.fetch("""
            SELECT tc.name AS course,
                   ROUND(100.0 * SUM(CASE WHEN et.status = 'Expired' THEN 1 ELSE 0 END) / COUNT(*), 1) AS expired_pct
            FROM employee_training et
            JOIN training_courses tc ON et.course_id = tc.id
            GROUP BY tc.name
            ORDER BY expired_pct DESC
            LIMIT 5
        """)

    total = int(totals["total"] or 1)
    result = {
        "current":       int(totals["current"] or 0),
        "expiring_soon": int(totals["expiring_soon"] or 0),
        "expired":       int(totals["expired"] or 0),
        "compliance_rate": round(100.0 * int(totals["current"] or 0) / total, 1),
        "worst_courses": [{"course": r["course"], "expired_pct": float(r["expired_pct"])} for r in worst],
    }
    cache.set("security_compliance", result)
    return result
