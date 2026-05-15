import enum
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.config.database import Base
from src.models.base import BaseModel


class SubscriptionTier(str, enum.Enum):
    """Subscription tier types"""
    STANDARD = "standard"
    PRO = "pro"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status types"""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"


class Subscription(Base, BaseModel):
    """
    User subscription model
    
    Tracks subscription tier and Stripe integration.
    Standard tier is free (no Stripe).
    Pro tier is paid (one-time payment, lifetime access).
    """
    __tablename__ = "subscriptions"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_subscription_id = Column(String, nullable=True, unique=True, index=True)
    stripe_checkout_session_id = Column(String, nullable=True, index=True)
    tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.STANDARD, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    is_lifetime = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship to user
    user = relationship("User", back_populates="subscription")
    
    def __repr__(self):
        return f"<Subscription {self.user_id}: {self.tier.value}>"
    
    @property
    def is_pro(self) -> bool:
        """Check if user has Pro tier"""
        return self.tier == SubscriptionTier.PRO
    
    @property
    def is_active_pro(self) -> bool:
        """Check if user has active Pro subscription"""
        if self.tier != SubscriptionTier.PRO:
            return False
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    @property
    def can_access_pro_features(self) -> bool:
        """Check if user can access Pro features"""
        return self.is_active_pro
