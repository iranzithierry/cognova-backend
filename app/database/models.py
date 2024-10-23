from sqlalchemy.orm import DeclarativeBase
from repository import Repository
from uuid import UUID
import uuid
from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from enum import Enum


class CognovaEntity(DeclarativeBase, Repository):
    @declared_attr
    def id(cls) -> Mapped[UUID]:
        if not hasattr(cls, "__no_id__"):
            return mapped_column(
                UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
            )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"
    

class BillingCycle(Enum):
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
    ONCE = "ONCE"


class PaymentStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"


class PaymentMethodStatus(Enum):
    UNACTIVE = "UNACTIVE"
    ACTIVE = "ACTIVE"
    FUTURE = "FUTURE"
