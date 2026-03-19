from fastapi import APIRouter
import db, cache

router = APIRouter()


@router.get("/dept-risk")
async def dept_risk():
    cached = cache.get("graph_dept_risk")
    if cached:
        return cached
    async with db.neo4j_driver.session() as s:
        result = await s.run("""
            MATCH (d:Department)<-[:WORKS_IN]-(e:Employee)-[:ASSIGNED_TO]->(l:Laptop)-[:HAD_INCIDENT]->(i:Incident)
            WHERE i.status IN ['Open', 'In Progress']
            RETURN d.name AS dept, COUNT(i) AS open_incidents
            ORDER BY open_incidents DESC
        """)
        rows = await result.data()
    data = {"departments": [{"dept": r["dept"], "open_incidents": r["open_incidents"]} for r in rows]}
    cache.set("graph_dept_risk", data)
    return data


@router.get("/app-exposure")
async def app_exposure():
    cached = cache.get("graph_app_exposure")
    if cached:
        return cached
    async with db.neo4j_driver.session() as s:
        result = await s.run("""
            MATCH (l:Laptop)-[:HAD_INCIDENT]->(i:Incident)
            WHERE i.status IN ['Open', 'In Progress']
            WITH DISTINCT l
            MATCH (l)-[:HAS_INSTALLED]->(a:Application)
            RETURN a.name AS app, COUNT(DISTINCT l) AS affected_devices
            ORDER BY affected_devices DESC
            LIMIT 10
        """)
        rows = await result.data()
    data = {"apps": [{"app": r["app"], "affected_devices": r["affected_devices"]} for r in rows]}
    cache.set("graph_app_exposure", data)
    return data
