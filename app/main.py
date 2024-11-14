from prisma import Prisma
from app.core.database import db
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.api.routes import chat as chats_router, sources as sources_router

app = FastAPI(title="Cognova API", version="1.0.0", docs_url="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(sources_router.router, prefix="/api/v1/sources", tags=["sources"])
app.include_router(chats_router.router, prefix="/api/v1/bots", tags=["chat"])


@app.on_event("startup")
async def startup():
    await db.connect()


@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()
