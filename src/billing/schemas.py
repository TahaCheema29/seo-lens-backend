from typing import Optional

from pydantic import BaseModel, Field


class CheckoutSessionRequest(BaseModel):
    success_path: str = Field(default="/billing/success", max_length=512)
    cancel_path: str = Field(default="/billing/cancel", max_length=512)


class SubscriptionInfoResponse(BaseModel):
    plan_code: str
    status: str
    stripe_subscription_id: Optional[str]
    current_period_end: Optional[str]
    cancel_at_period_end: bool

    class Config:
        from_attributes = True
