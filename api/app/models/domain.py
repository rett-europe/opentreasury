from enum import Enum


class AuditAction(str, Enum):
    CREATE = "Create"
    UPDATE = "Update"
    DELETE = "Delete"


class CategoryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    REFUND = "refund"


class CategorizationStatus(str, Enum):
    UNCATEGORIZED = "uncategorized"
    MANUALLY_CATEGORIZED = "manually_categorized"
    AUTO_CATEGORIZED = "auto_categorized"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    FLAGGED = "flagged"
