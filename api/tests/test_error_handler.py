"""Tests for middleware/error_handler.py — custom exception handlers."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.middleware.error_handler import register_error_handlers


@pytest.fixture
async def error_app():
    """
    A minimal FastAPI app with the error handlers registered and dedicated
    routes that raise specific exceptions.
    """
    from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceNotFoundError

    app = FastAPI()
    register_error_handlers(app)

    @app.get("/raise-cosmos-404")
    async def raise_cosmos_404():
        raise CosmosResourceNotFoundError(status_code=404, message="not found")

    @app.get("/raise-cosmos-409")
    async def raise_cosmos_409():
        raise CosmosHttpResponseError(status_code=409, message="conflict")

    @app.get("/raise-cosmos-429")
    async def raise_cosmos_429():
        err = CosmosHttpResponseError(status_code=429, message="too many requests")
        err.headers = {"x-ms-retry-after-ms": "1000"}
        raise err

    @app.get("/raise-cosmos-500")
    async def raise_cosmos_500():
        raise CosmosHttpResponseError(status_code=500, message="internal error")

    @app.get("/raise-generic")
    async def raise_generic():
        raise RuntimeError("unexpected boom")

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        yield client


class TestErrorHandlers:
    async def test_cosmos_not_found_returns_404(self, error_app):
        response = await error_app.get("/raise-cosmos-404")
        assert response.status_code == 404
        assert response.json() == {"detail": "Resource not found"}

    async def test_cosmos_conflict_returns_409(self, error_app):
        response = await error_app.get("/raise-cosmos-409")
        assert response.status_code == 409
        assert response.json() == {"detail": "Resource conflict"}

    async def test_cosmos_rate_limit_returns_429(self, error_app):
        response = await error_app.get("/raise-cosmos-429")
        assert response.status_code == 429
        assert response.json() == {"detail": "Too many requests, please retry later"}

    async def test_cosmos_other_error_returns_502(self, error_app):
        response = await error_app.get("/raise-cosmos-500")
        assert response.status_code == 502
        assert response.json() == {"detail": "Database operation failed"}

    async def test_generic_exception_returns_500(self, error_app):
        response = await error_app.get("/raise-generic")
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error"}
