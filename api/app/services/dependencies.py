from fastapi import Depends

from app.repositories.dependencies import (
    get_audit_repo,
    get_category_repo,
    get_reference_item_repo,
    get_transaction_repo,
)
from app.services.account_service import AccountService
from app.services.audit_service import AuditService
from app.services.category_service import CategoryService
from app.services.export_service import ExportService
from app.services.import_service import ImportService
from app.services.reference_data_service import ReferenceDataService
from app.services.report_service import ReportService
from app.services.tag_service import TagService
from app.services.transaction_service import TransactionService


def get_audit_service(
    repo=Depends(get_audit_repo),
) -> AuditService:
    return AuditService(repo=repo)


def get_transaction_service(
    repo=Depends(get_transaction_repo),
    audit_service: AuditService = Depends(get_audit_service),
    category_repo=Depends(get_category_repo),
) -> TransactionService:
    return TransactionService(repo=repo, audit_service=audit_service, category_repo=category_repo)


def get_account_service(
    repo=Depends(get_reference_item_repo),
    audit_service: AuditService = Depends(get_audit_service),
    transaction_repo=Depends(get_transaction_repo),
) -> AccountService:
    return AccountService(repo=repo, audit_service=audit_service, transaction_repo=transaction_repo)


def get_tag_service(
    repo=Depends(get_reference_item_repo),
    audit_service: AuditService = Depends(get_audit_service),
    transaction_repo=Depends(get_transaction_repo),
) -> TagService:
    return TagService(repo=repo, audit_service=audit_service, transaction_repo=transaction_repo)


def get_category_service(
    repo=Depends(get_category_repo),
    audit_service: AuditService = Depends(get_audit_service),
    transaction_repo=Depends(get_transaction_repo),
) -> CategoryService:
    return CategoryService(repo=repo, audit_service=audit_service, transaction_repo=transaction_repo)


def get_export_service(
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> ExportService:
    return ExportService(transaction_service=transaction_service)


def get_import_service(
    account_service: AccountService = Depends(get_account_service),
    category_service: CategoryService = Depends(get_category_service),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> ImportService:
    return ImportService(
        account_service=account_service,
        category_service=category_service,
        transaction_service=transaction_service,
    )


def get_report_service(
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> ReportService:
    return ReportService(transaction_service=transaction_service)


def get_reference_data_service(
    account_service: AccountService = Depends(get_account_service),
    category_service: CategoryService = Depends(get_category_service),
    tag_service: TagService = Depends(get_tag_service),
) -> ReferenceDataService:
    return ReferenceDataService(
        account_service=account_service,
        category_service=category_service,
        tag_service=tag_service,
    )
