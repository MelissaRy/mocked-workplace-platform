from fastapi import APIRouter
import db, cache

router = APIRouter()


@router.get("/by-status")
async def by_status():
    cached = cache.get("fleet_status")
    if cached:
        return cached
    async with db.pg_pool.acquire() as conn:
        rows = await conn.fetch("SELECT status, COUNT(*) AS count FROM laptops GROUP BY status ORDER BY count DESC")
    result = {"data": [{"status": r["status"], "count": r["count"]} for r in rows]}
    cache.set("fleet_status", result)
    return result


@router.get("/by-os")
async def by_os():
    cached = cache.get("fleet_os")
    if cached:
        return cached
    async with db.pg_pool.acquire() as conn:
        rows = await conn.fetch("SELECT os, COUNT(*) AS count FROM laptops GROUP BY os ORDER BY count DESC")
    result = {"data": [{"os": r["os"], "count": r["count"]} for r in rows]}
    cache.set("fleet_os", result)
    return result


@router.get("/by-make")
async def by_make():
    cached = cache.get("fleet_make")
    if cached:
        return cached
    async with db.pg_pool.acquire() as conn:
        rows = await conn.fetch("SELECT make, COUNT(*) AS count FROM laptops GROUP BY make ORDER BY count DESC")
    result = {"data": [{"make": r["make"], "count": r["count"]} for r in rows]}
    cache.set("fleet_make", result)
    return result


@router.get("/metrics-distribution")
async def metrics_distribution():
    cached = cache.get("fleet_metrics_dist")
    if cached:
        return cached
    async with db.pg_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
              CASE WHEN cpu_usage_pct <= 25 THEN '0-25'
                   WHEN cpu_usage_pct <= 50 THEN '26-50'
                   WHEN cpu_usage_pct <= 75 THEN '51-75'
                   ELSE '76-100' END AS bucket,
              COUNT(*) AS cpu_count,
              SUM(CASE WHEN ram_usage_pct <= 25 THEN 1 ELSE 0 END) AS ram_low,
              SUM(CASE WHEN ram_usage_pct <= 50 THEN 1 ELSE 0 END) AS ram_med,
              SUM(CASE WHEN disk_usage_pct > 90 THEN 1 ELSE 0 END) AS disk_critical
            FROM laptop_metrics
            GROUP BY bucket
            ORDER BY bucket
        """)
        disk = await conn.fetch("""
            SELECT
              CASE WHEN disk_usage_pct <= 50 THEN '0-50'
                   WHEN disk_usage_pct <= 75 THEN '51-75'
                   WHEN disk_usage_pct <= 90 THEN '76-90'
                   ELSE '91-100' END AS bucket,
              COUNT(*) AS count
            FROM laptop_metrics GROUP BY bucket ORDER BY bucket
        """)
        ram = await conn.fetch("""
            SELECT
              CASE WHEN ram_usage_pct <= 25 THEN '0-25'
                   WHEN ram_usage_pct <= 50 THEN '26-50'
                   WHEN ram_usage_pct <= 75 THEN '51-75'
                   ELSE '76-100' END AS bucket,
              COUNT(*) AS count
            FROM laptop_metrics GROUP BY bucket ORDER BY bucket
        """)
        cpu = await conn.fetch("""
            SELECT
              CASE WHEN cpu_usage_pct <= 25 THEN '0-25'
                   WHEN cpu_usage_pct <= 50 THEN '26-50'
                   WHEN cpu_usage_pct <= 75 THEN '51-75'
                   ELSE '76-100' END AS bucket,
              COUNT(*) AS count
            FROM laptop_metrics GROUP BY bucket ORDER BY bucket
        """)
    result = {
        "cpu":  {r["bucket"]: r["count"] for r in cpu},
        "ram":  {r["bucket"]: r["count"] for r in ram},
        "disk": {r["bucket"]: r["count"] for r in disk},
    }
    cache.set("fleet_metrics_dist", result)
    return result
