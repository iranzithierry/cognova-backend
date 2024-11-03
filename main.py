from fastapi import FastAPI
from app.routers import chat as chat_router, sources as sources_router

app = FastAPI(title="Cognova API", version="1.0.0", docs_url="/api/v1")

app.include_router(sources_router.router, prefix="/api/v1/sources", tags=["sources"])
app.include_router(chat_router.router, prefix="/api/v1/bots", tags=["chat"])
