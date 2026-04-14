from app.repositories.cosmos.audit_repo import CosmosAuditRepository
from app.repositories.cosmos.category_repo import CosmosCategoryRepository
from app.repositories.cosmos.reference_item_repo import CosmosReferenceItemRepository
from app.repositories.cosmos.transaction_repo import CosmosTransactionRepository
from app.repositories.cosmos.user_preferences_repo import CosmosUserPreferencesRepository

_transaction_repo = CosmosTransactionRepository()
_reference_item_repo = CosmosReferenceItemRepository()
_category_repo = CosmosCategoryRepository()
_audit_repo = CosmosAuditRepository()
_user_preferences_repo = CosmosUserPreferencesRepository()


def get_transaction_repo() -> CosmosTransactionRepository:
    return _transaction_repo


def get_reference_item_repo() -> CosmosReferenceItemRepository:
    return _reference_item_repo


def get_category_repo() -> CosmosCategoryRepository:
    return _category_repo


def get_audit_repo() -> CosmosAuditRepository:
    return _audit_repo


def get_user_preferences_repo() -> CosmosUserPreferencesRepository:
    return _user_preferences_repo
