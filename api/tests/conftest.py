"""
Shared pytest fixtures for OpenTreasury API tests.

Provides:
- Mock Cosmos DB containers (async)
- Mock auth (fake JWT tokens with example-ngo.org tenant claims)
- FastAPI TestClient via httpx
- Sample data factories
"""

import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

# ---------------------------------------------------------------------------
# Set required environment variables before any app module is imported.
# pydantic-settings reads these at Settings() instantiation time.
# ---------------------------------------------------------------------------
os.environ.setdefault("AZURE_TENANT_ID", "test-tenant-id-00000000")
os.environ.setdefault("AZURE_CLIENT_ID", "test-client-id-00000000")
os.environ.setdefault("COSMOS_ENDPOINT", "https://test.documents.azure.com:443/")
os.environ.setdefault("COSMOS_DATABASE_NAME", "test-db")

# ---------------------------------------------------------------------------
# Async iterator helper (simulates Cosmos DB query_items async generator)
# ---------------------------------------------------------------------------


class AsyncIteratorMock:
    """Wraps a list so it can be used as an async iterator (like Cosmos query_items)."""

    def __init__(self, items: list[dict]):
        self._items = items
        self._index = 0

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self):
        if self._index >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._index]
        self._index += 1
        return item


# ---------------------------------------------------------------------------
# Sample data helpers
# ---------------------------------------------------------------------------


def make_transaction(**overrides) -> dict[str, Any]:
    """Factory for transaction documents."""
    base = {
        "id": f"tx-{uuid.uuid4().hex[:8]}",
        "type": "transaction",
        "date": "2026-04-10",
        "year": 2026,
        "month": 4,
        "amount": Decimal("150.50"),
        "transactionType": "income",
        "categoryId": "cat-001",
        "subcategoryId": "subcat-001",
        "categorizationStatus": "manually_categorized",
        "reviewStatus": "approved",
        "sourceReference": None,
        "counterpartyName": None,
        "counterpartyReference": None,
        "reviewedBy": None,
        "reviewedByName": None,
        "reviewedAt": None,
        "originalAmount": None,
        "originalDate": None,
        "notes": [],
        "description": "Monthly donation",
        "reference": "DNT-2026-04-001",
        "createdBy": "test-user-oid-abc123",
        "createdAt": "2026-04-10T14:30:00Z",
        "updatedBy": None,
        "updatedAt": None,
        "isDeleted": False,
    }
    base.update(overrides)
    return base


def make_category(**overrides) -> dict[str, Any]:
    """Factory for category documents."""
    base = {
        "id": "cat-001",
        "type": "category",
        "name": "Donations",
        "description": "Income from donors",
        "categoryType": "income",
        "subcategories": [
            {"id": "subcat-001", "name": "Individual Donors"},
            {"id": "subcat-002", "name": "Corporate Sponsors"},
        ],
        "createdAt": "2026-04-01T10:00:00Z",
    }
    base.update(overrides)
    return base


def make_audit_entry(**overrides) -> dict[str, Any]:
    """Factory for audit trail documents."""
    base = {
        "id": f"audit-{uuid.uuid4().hex[:8]}",
        "entityType": "Transaction",
        "entityId": "tx-001",
        "action": "Create",
        "changedBy": "test-user-oid-abc123",
        "changedAt": "2026-04-10T14:30:00Z",
        "oldValues": {},
        "newValues": {"amount": 150.50, "transactionType": "Income"},
        "ttl": 220752000,  # ~7 years
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Fake JWT / Auth fixtures
# ---------------------------------------------------------------------------

RETT_ES_TENANT_ID = "rett-es-tenant-id-fake-0001"
WRONG_TENANT_ID = "wrong-tenant-id-fake-9999"
TEST_USER_OID = "test-user-oid-abc123"
TEST_USER_EMAIL = "testuser@example-ngo.org"


def make_token_claims(**overrides) -> dict[str, Any]:
    """
    Generates fake decoded JWT claims that mimic a valid Entra ID token
    from the example-ngo.org tenant.
    """
    now = int(datetime.now(timezone.utc).timestamp())
    base = {
        "aud": "api://ngo-treasury-api",
        "iss": f"https://login.microsoftonline.com/{RETT_ES_TENANT_ID}/v2.0",
        "iat": now - 300,
        "nbf": now - 300,
        "exp": now + 3600,  # valid for 1 hour
        "oid": TEST_USER_OID,
        "preferred_username": TEST_USER_EMAIL,
        "tid": RETT_ES_TENANT_ID,
        "scp": "access",
        "name": "Test User",
        "sub": "subject-id-fake",
    }
    base.update(overrides)
    return base


def make_expired_token_claims() -> dict[str, Any]:
    """Token that expired 1 hour ago."""
    now = int(datetime.now(timezone.utc).timestamp())
    return make_token_claims(
        iat=now - 7200,
        nbf=now - 7200,
        exp=now - 3600,  # expired
    )


def make_wrong_tenant_claims() -> dict[str, Any]:
    """Token from a different tenant (not example-ngo.org)."""
    return make_token_claims(
        tid=WRONG_TENANT_ID,
        iss=f"https://login.microsoftonline.com/{WRONG_TENANT_ID}/v2.0",
    )


def make_missing_scope_claims() -> dict[str, Any]:
    """Token with no 'access' scope."""
    claims = make_token_claims()
    claims.pop("scp", None)
    return claims


def make_missing_oid_claims() -> dict[str, Any]:
    """Token missing the oid claim."""
    claims = make_token_claims()
    claims.pop("oid", None)
    return claims


@pytest.fixture
def valid_auth_header() -> dict[str, str]:
    """Authorization header with a fake valid Bearer token."""
    return {"Authorization": "Bearer fake-valid-token-for-testing"}


@pytest.fixture
def expired_auth_header() -> dict[str, str]:
    return {"Authorization": "Bearer fake-expired-token"}


@pytest.fixture
def wrong_tenant_auth_header() -> dict[str, str]:
    return {"Authorization": "Bearer fake-wrong-tenant-token"}


@pytest.fixture
def no_auth_header() -> dict[str, str]:
    return {}


@pytest.fixture
def malformed_auth_header() -> dict[str, str]:
    return {"Authorization": "NotBearer some-garbage"}


# ---------------------------------------------------------------------------
# Mock Cosmos DB fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_transactions_container() -> AsyncMock:
    """
    Mock Cosmos DB container for transactions.
    Pre-configured with common operations returning sensible defaults.
    Override return_value in individual tests as needed.
    """
    container = AsyncMock()

    sample_tx = make_transaction()

    # query_items returns async iterator
    container.query_items.return_value = AsyncIteratorMock([sample_tx])

    # Single item reads
    container.read_item.return_value = sample_tx

    # Create returns the created item
    container.create_item.return_value = sample_tx

    # Upsert returns the upserted item
    container.upsert_item.return_value = sample_tx

    # Patch returns the patched item
    container.patch_item.return_value = {**sample_tx, "isDeleted": True}

    return container


@pytest.fixture
def mock_categories_container() -> AsyncMock:
    """Mock Cosmos DB container for categories."""
    container = AsyncMock()

    sample_cat = make_category()

    container.query_items.return_value = AsyncIteratorMock([sample_cat])
    container.read_item.return_value = sample_cat
    container.create_item.return_value = sample_cat
    container.upsert_item.return_value = sample_cat

    return container


@pytest.fixture
def mock_audit_container() -> AsyncMock:
    """Mock Cosmos DB container for audit_log."""
    container = AsyncMock()

    sample_audit = make_audit_entry()

    container.query_items.return_value = AsyncIteratorMock([sample_audit])
    container.create_item.return_value = sample_audit

    return container


@pytest.fixture
def mock_cosmos_database(
    mock_transactions_container,
    mock_categories_container,
    mock_audit_container,
) -> AsyncMock:
    """
    Mock Cosmos DB database with all three containers.
    Usage in tests: monkeypatch the CosmosService to return this.
    """
    db = AsyncMock()

    def get_container(name: str):
        containers = {
            "transactions": mock_transactions_container,
            "categories": mock_categories_container,
            "audit_log": mock_audit_container,
        }
        return containers.get(name, AsyncMock())

    db.get_container_client.side_effect = get_container
    return db


# ---------------------------------------------------------------------------
# Cosmos DB resilience test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cosmos_429_error():
    """Simulates a Cosmos DB 429 (Too Many Requests) response."""
    from azure.cosmos.exceptions import CosmosHttpResponseError

    error = CosmosHttpResponseError(
        status_code=429,
        message="Request rate too large",
    )
    error.headers = {"x-ms-retry-after-ms": "1000"}
    return error


@pytest.fixture
def cosmos_404_error():
    """Simulates a Cosmos DB 404 (Not Found) response."""
    from azure.cosmos.exceptions import CosmosResourceNotFoundError

    return CosmosResourceNotFoundError(
        status_code=404,
        message="Entity with the specified id does not exist",
    )


@pytest.fixture
def cosmos_409_error():
    """Simulates a Cosmos DB 409 (Conflict) response."""
    from azure.cosmos.exceptions import CosmosResourceExistsError

    return CosmosResourceExistsError(
        status_code=409,
        message="Entity with the specified id already exists",
    )


# ---------------------------------------------------------------------------
# Financial edge case data
# ---------------------------------------------------------------------------


@pytest.fixture
def financial_edge_transactions() -> list[dict]:
    """Transactions designed to stress financial precision."""
    return [
        make_transaction(id="tx-penny", amount=Decimal("0.01"), description="Minimum amount"),
        make_transaction(id="tx-max", amount=Decimal("999999.99"), description="Practical max"),
        make_transaction(id="tx-round-1", amount=Decimal("0.10"), description="Rounding test 0.1"),
        make_transaction(id="tx-round-2", amount=Decimal("0.20"), description="Rounding test 0.2"),
        make_transaction(id="tx-many-small", amount=Decimal("0.01"), description="Many small 1"),
        make_transaction(id="tx-many-small-2", amount=Decimal("0.01"), description="Many small 2"),
        make_transaction(id="tx-many-small-3", amount=Decimal("0.01"), description="Many small 3"),
    ]


@pytest.fixture
def precision_sum_transactions() -> list[dict]:
    """1000 transactions at €0.01 each — sum must be exactly €10.00."""
    return [make_transaction(id=f"tx-micro-{i:04d}", amount=Decimal("0.01")) for i in range(1000)]


# ---------------------------------------------------------------------------
# FastAPI TestClient (async via httpx)
# ---------------------------------------------------------------------------

FAKE_ADMIN_USER = {
    "oid": TEST_USER_OID,
    "name": "Test User",
    "email": TEST_USER_EMAIL,
    "roles": ["Admin"],
    "role": "Admin",
}

FAKE_VIEWER_USER = {
    "oid": "viewer-oid-xyz",
    "name": "Viewer User",
    "email": "viewer@example-ngo.org",
    "roles": [],
    "role": "Viewer",
}


@pytest.fixture
async def admin_client():
    """
    Async HTTP client wired to the FastAPI app with auth overridden to
    return an Admin user. ASGITransport does not trigger the lifespan,
    so no real Cosmos DB connection is needed.
    """
    from httpx import ASGITransport, AsyncClient

    from app.auth.dependencies import get_current_admin, get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: FAKE_ADMIN_USER
    app.dependency_overrides[get_current_admin] = lambda: FAKE_ADMIN_USER

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def viewer_client():
    """
    Async HTTP client wired to the FastAPI app with auth overridden to
    return a Viewer (non-admin) user. The real get_current_admin will
    raise 403 for admin-only endpoints.
    """
    from httpx import ASGITransport, AsyncClient

    from app.auth.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: FAKE_VIEWER_USER

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
