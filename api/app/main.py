from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.error_handler import register_error_handlers
from app.routers import (
    accounts,
    audit,
    categories,
    export,
    imports,
    reference_data,
    reports,
    split,
    tags,
    transactions,
    user,
)
from app.services.cosmos_client import cosmos_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    await cosmos_service.initialize(
        endpoint=settings.COSMOS_ENDPOINT,
        database_name=settings.COSMOS_DATABASE_NAME,
        key=settings.COSMOS_KEY,
    )
    yield
    await cosmos_service.close()


app = FastAPI(
    title="OpenTreasury API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(transactions.router)
app.include_router(split.router)
app.include_router(categories.router)
app.include_router(accounts.router)
app.include_router(tags.router)
app.include_router(reports.router)
app.include_router(export.router)
app.include_router(imports.router)
app.include_router(reference_data.router)
app.include_router(user.router)
app.include_router(audit.router)


@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "ok"}
