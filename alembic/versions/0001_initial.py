"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reference", sa.String(100), nullable=False, unique=True),
        sa.Column("paystack_id", sa.BigInteger(), nullable=True),
        sa.Column("amount_kobo", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(5), nullable=False, server_default="NGN"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("customer_email", sa.String(255), nullable=True),
        sa.Column("customer_name", sa.String(255), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_response", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_transactions_reference", "transactions", ["reference"])
    op.create_index("ix_transactions_status", "transactions", ["status"])
    op.create_index("ix_transactions_customer_email", "transactions", ["customer_email"])
    op.create_index("ix_transactions_paid_at", "transactions", ["paid_at"])

    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("telegram_username", sa.String(100), nullable=True),
        sa.Column("telegram_first_name", sa.String(100), nullable=True),
        sa.Column("telegram_last_name", sa.String(100), nullable=True),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transactions.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("access_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("access_expiry", sa.DateTime(timezone=True), nullable=False),
        sa.Column("classroom_invite_link", sa.Text(), nullable=True),
        sa.Column("discussion_invite_link", sa.Text(), nullable=True),
        sa.Column("classroom_joined", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("discussion_joined", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_students_telegram_id", "students", ["telegram_id"])
    op.create_index("ix_students_access_expiry", "students", ["access_expiry"])
    op.create_index("ix_students_revoked", "students", ["revoked"])
    op.create_index("ix_students_expiry_revoked", "students", ["access_expiry", "revoked"])

    op.create_table(
        "webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_webhook_events_source", "webhook_events", ["source"])


def downgrade() -> None:
    op.drop_table("webhook_events")
    op.drop_table("students")
    op.drop_table("transactions")
