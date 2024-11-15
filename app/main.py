import logging
from app.core.database import db
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from app.api.routes import chat as chats_router, sources as sources_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await db.connect()
        yield
    finally:
        # Shutdown
        await db.disconnect()


app = FastAPI(
    title="Cognova API",
    version="1.0.0",
    docs_url="/api/v1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_db():
    if not await db.verify_connection():
        try:
            await db.connect()
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise HTTPException(status_code=503, detail="Database connection error")
    return db.prisma


# Use the dependency in your routes
app.include_router(
    sources_router.router,
    prefix="/api/v1/sources",
    tags=["sources"],
    dependencies=[Depends(verify_db)],
)
app.include_router(
    chats_router.router,
    prefix="/api/v1/bots",
    tags=["chat"],
    dependencies=[Depends(verify_db)],
)
