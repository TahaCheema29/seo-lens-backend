import enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.config.database import Base
from .base import BaseModel


class PlanCode(str, enum.Enum):
    BASIC = "basic"
    PRO = "pro"


class SubscriptionStatus(str, enum.Enum):
    """Mirrors Stripe subscription statuses; BASIC tier uses ACTIVE only."""

    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"


class UserSubscription(Base, BaseModel):
    __tablename__ = "user_subscriptions"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    plan_code = Column(
        SAEnum(PlanCode, name="plancode", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PlanCode.BASIC,
    )
    stripe_subscription_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_price_id = Column(String(255), nullable=True)
    status = Column(
        SAEnum(
            SubscriptionStatus,
            name="subscriptionstatus",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=SubscriptionStatus.ACTIVE,
    )
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="subscription")


class StripeWebhookEvent(Base, BaseModel):
    __tablename__ = "stripe_webhook_events"

    stripe_event_id = Column(String(255), unique=True, nullable=False, index=True)
