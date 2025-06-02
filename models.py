from dataclasses import dataclass
from datetime import datetime
from enum import unique, Enum
from typing import Optional, List


@dataclass(frozen=True)
class RuleData:
    name: str
    description: str
    ip: str
    expired_date: Optional[datetime] = None


@unique
class Operation(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


@dataclass(frozen=True)
class RuleOperation:
    operation: Operation
    customer_id: int
    rule_name: Optional[str] = None
    rule_data: Optional[RuleData] = None


@dataclass(frozen=True)
class BulkOperationsRequest:
    operations: List[RuleOperation]
