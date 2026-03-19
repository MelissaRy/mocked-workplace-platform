import os
from contextlib import asynccontextmanager
import asyncpg
from neo4j import AsyncGraphDatabase

PG_DSN      = os.getenv("PG_DSN",      "postgresql://workplace:__REDACTED__@localhost:5433/workplace_db")
NEO4J_URI   = os.getenv("NEO4J_URI",   "bolt://localhost:7688")
NEO4J_USER  = os.getenv("NEO4J_USER",  "neo4j")
NEO4J_PASS  = os.getenv("NEO4J_PASS",  "__REDACTED__")

pg_pool     = None
neo4j_driver = None


@asynccontextmanager
async def lifespan(app):
    global pg_pool, neo4j_driver
    pg_pool = await asyncpg.create_pool(dsn=PG_DSN, min_size=2, max_size=10)
    neo4j_driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    await neo4j_driver.verify_connectivity()
    yield
    await pg_pool.close()
    await neo4j_driver.close()
