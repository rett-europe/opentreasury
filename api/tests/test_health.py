"""Smoke test — verifies basic module imports work."""


def test_models_import():
    """Ensure domain models can be imported without side effects."""
    from app.models.domain import AuditAction

    assert AuditAction.CREATE.value == "Create"


def test_repository_protocols_import():
    """Ensure repository protocols can be imported."""
    from app.repositories.protocols import TransactionRepository, AuditRepository

    assert TransactionRepository is not None
    assert AuditRepository is not None
