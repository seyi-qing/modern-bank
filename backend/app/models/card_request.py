"""Card issuance requests — pending until card ops / admin approve."""
from datetime import datetime, timezone
from decimal import Decimal
import enum

from sqlalchemy import String, DateTime, Enum as SAEnum, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import CardType


class CardRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


def _enum_values(enum_cls):
    return [e.value for e in enum_cls]


class CardRequest(Base):
    __tablename__ = "card_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    card_type: Mapped[CardType] = mapped_column(
        SAEnum(
            CardType,
            name="cardtype",
            values_callable=_enum_values,
            create_constraint=False,
            native_enum=True,
        ),
        default=CardType.VIRTUAL,
    )
    label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    spending_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    status: Mapped[CardRequestStatus] = mapped_column(
        SAEnum(
            CardRequestStatus,
            name="cardrequeststatus",
            values_callable=_enum_values,
            create_constraint=False,
            native_enum=True,
        ),
        default=CardRequestStatus.PENDING,
        index=True,
    )
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    issued_card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
