import logging

from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceNotFoundError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("opentreasury")


def register_error_handlers(app: FastAPI):
    @app.exception_handler(CosmosResourceNotFoundError)
    async def cosmos_not_found_handler(request: Request, exc: CosmosResourceNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": "Resource not found"},
        )

    @app.exception_handler(CosmosHttpResponseError)
    async def cosmos_error_handler(request: Request, exc: CosmosHttpResponseError):
        logger.error("Cosmos DB error: status=%s message=%s", exc.status_code, exc.message)

        if exc.status_code == 409:
            return JSONResponse(
                status_code=409,
                content={"detail": "Resource conflict"},
            )
        if exc.status_code == 429:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests, please retry later"},
            )

        return JSONResponse(
            status_code=502,
            content={"detail": "Database operation failed"},
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
