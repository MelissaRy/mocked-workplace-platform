import os
from contextlib import asynccontextmanager
import asyncpg
from neo4j import AsyncGraphDatabase

PG_DSN      = os.environ["PG_DSN"]
NEO4J_URI   = os.environ["NEO4J_URI"]
NEO4J_USER  = os.environ["NEO4J_USER"]
NEO4J_PASS  = os.environ["NEO4J_PASS"]

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
