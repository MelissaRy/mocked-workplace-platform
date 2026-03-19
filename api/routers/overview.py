from fastapi import APIRouter
import db, cache

router = APIRouter()


@router.get("/overview")
async def get_overview():
    cached = cache.get("overview")
    if cached:
        return cached

    async with db.pg_pool.acquire() as conn:
        row = await conn.fetchrow("""
            WITH
              device_stats AS (
                SELECT
                  COUNT(*) AS total,
                  ROUND(100.0 * SUM(CASE WHEN managed THEN 1 ELSE 0 END) / COUNT(*), 1) AS managed_pct,
                  ROUND(100.0 * SUM(CASE WHEN disk_encrypted THEN 1 ELSE 0 END) / COUNT(*), 1) AS encrypted_pct,
                  SUM(CASE WHEN warranty_expiry < CURRENT_DATE THEN 1 ELSE 0 END) AS warranty_expired
                FROM laptops
              ),
              metric_stats AS (
                SELECT
                  ROUND(AVG(os_patches_missing), 1) AS avg_patches,
                  ROUND(100.0 * SUM(CASE WHEN antivirus_status = 'OK' THEN 1 ELSE 0 END) / COUNT(*), 1) AS av_ok_pct
                FROM laptop_metrics
              ),
              incident_stats AS (
                SELECT
                  SUM(CASE WHEN status != 'Resolved' THEN 1 ELSE 0 END) AS active_inc,
                  SUM(CASE WHEN severity = 'Critical' AND status != 'Resolved' THEN 1 ELSE 0 END) AS critical_inc
                FROM incidents
              ),
              employee_stats AS (
                SELECT COUNT(*) AS total_emp FROM employees
              ),
              training_stats AS (
                SELECT ROUND(100.0 * SUM(CASE WHEN status = 'Expired' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS expired_pct
                FROM employee_training
              )
            SELECT
              e.total_emp,
              d.total,
              d.managed_pct,
              d.encrypted_pct,
              d.warranty_expired,
              m.avg_patches,
              m.av_ok_pct,
              i.active_inc,
              i.critical_inc,
              t.expired_pct
            FROM device_stats d, metric_stats m, incident_stats i, employee_stats e, training_stats t
        """)

    result = {
        "total_employees":       int(row["total_emp"]),
        "total_devices":         int(row["total"]),
        "managed_pct":           float(row["managed_pct"] or 0),
        "encrypted_pct":         float(row["encrypted_pct"] or 0),
        "warranty_expired_count": int(row["warranty_expired"] or 0),
        "avg_patches_missing":   float(row["avg_patches"] or 0),
        "antivirus_ok_pct":      float(row["av_ok_pct"] or 0),
        "active_incidents":      int(row["active_inc"] or 0),
        "critical_incidents":    int(row["critical_inc"] or 0),
        "training_expired_pct":  float(row["expired_pct"] or 0),
    }
    cache.set("overview", result)
    return result
