from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Transaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "transactions"

    reference: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    paystack_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    amount_kobo: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), nullable=False, default="NGN")
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    customer_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    raw_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<Transaction {self.reference} {self.status}>"
