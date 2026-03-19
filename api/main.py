from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from db import lifespan
import db
from routers import overview, fleet, security, incidents, graph

app = FastAPI(title="Workplace Fleet Health API", version="1.0.0", lifespan=lifespan)

templates = Jinja2Templates(directory="templates")


@app.get("/", include_in_schema=False)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/health", tags=["system"])
async def health():
    pg_ok, neo4j_ok = True, True
    try:
        async with db.pg_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except Exception:
        pg_ok = False
    try:
        async with db.neo4j_driver.session() as s:
            await s.run("RETURN 1")
    except Exception:
        neo4j_ok = False
    return {"status": "ok" if pg_ok and neo4j_ok else "degraded", "pg": pg_ok, "neo4j": neo4j_ok}


app.include_router(overview.router,   prefix="/api")
app.include_router(fleet.router,      prefix="/api/fleet")
app.include_router(security.router,   prefix="/api/security")
app.include_router(incidents.router,  prefix="/api/incidents")
app.include_router(graph.router,      prefix="/api/graph")
