"""billing and subscriptions

Revision ID: billing_001
Revises: add_status_column
Create Date: 2026-05-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "billing_001"
down_revision: Union[str, None] = "add_status_column"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("stripe_customer_id", sa.String(length=255), nullable=True))
    op.create_index(
        op.f("ix_users_stripe_customer_id"),
        "users",
        ["stripe_customer_id"],
        unique=True,
    )

    plancode = postgresql.ENUM("basic", "pro", name="plancode", create_type=True)
    plancode.create(op.get_bind(), checkfirst=True)

    subscriptionstatus = postgresql.ENUM(
        "active",
        "trialing",
        "past_due",
        "canceled",
        "unpaid",
        "incomplete",
        "incomplete_expired",
        "paused",
        name="subscriptionstatus",
        create_type=True,
    )
    subscriptionstatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "user_subscriptions",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_code", plancode, nullable=False, server_default="basic"),
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_price_id", sa.String(length=255), nullable=True),
        sa.Column("status", subscriptionstatus, nullable=False, server_default="active"),
        sa.Column("current_period_start", sa.DateTime(), nullable=True),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_user_subscriptions_user_id"), "user_subscriptions", ["user_id"], unique=True
    )
    op.create_index(
        op.f("ix_user_subscriptions_stripe_subscription_id"),
        "user_subscriptions",
        ["stripe_subscription_id"],
        unique=True,
    )

    op.create_table(
        "stripe_webhook_events",
        sa.Column("stripe_event_id", sa.String(length=255), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_event_id"),
    )
    op.create_index(
        op.f("ix_stripe_webhook_events_stripe_event_id"),
        "stripe_webhook_events",
        ["stripe_event_id"],
        unique=True,
    )

    op.execute(
        """
        INSERT INTO user_subscriptions (
            id, user_id, plan_code, status, cancel_at_period_end, created_at, updated_at
        )
        SELECT gen_random_uuid(), id, 'basic'::plancode, 'active'::subscriptionstatus,
               false, NOW(), NOW()
        FROM users
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_stripe_webhook_events_stripe_event_id"), table_name="stripe_webhook_events")
    op.drop_table("stripe_webhook_events")
    op.drop_index(
        op.f("ix_user_subscriptions_stripe_subscription_id"), table_name="user_subscriptions"
    )
    op.drop_index(op.f("ix_user_subscriptions_user_id"), table_name="user_subscriptions")
    op.drop_table("user_subscriptions")
    op.execute("DROP TYPE IF EXISTS subscriptionstatus")
    op.execute("DROP TYPE IF EXISTS plancode")
    op.drop_index(op.f("ix_users_stripe_customer_id"), table_name="users")
    op.drop_column("users", "stripe_customer_id")
