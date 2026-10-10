from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Student(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "students"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    telegram_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    telegram_first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    telegram_last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
    )
    transaction: Mapped["Transaction"] = relationship(lazy="joined")  # noqa: F821

    access_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    access_expiry: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    classroom_invite_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    discussion_invite_link: Mapped[str | None] = mapped_column(Text, nullable=True)

    classroom_joined: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    discussion_joined: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_students_expiry_revoked", "access_expiry", "revoked"),
    )

    def __repr__(self) -> str:
        return f"<Student tg={self.telegram_id} expiry={self.access_expiry}>"
