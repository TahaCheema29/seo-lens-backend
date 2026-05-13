import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_ERROR, RESPONSE_STATUS_SUCCESS
from src.core.security import get_current_user
from src.models.user import User
from src.billing.access import subscription_has_pro_access
from src.billing.schemas import CheckoutSessionRequest, SubscriptionInfoResponse
from src.billing.subscription_repository import SubscriptionRepository
from src.billing.billing_service import create_pro_checkout_session, retrieve_checkout_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/subscription")
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = SubscriptionRepository(db)
    sub = await repo.get_by_user_id(current_user.id)
    if not sub:
        sub = await repo.ensure_basic(current_user.id)
    data = SubscriptionInfoResponse(
        plan_code=sub.plan_code.value,
        status=sub.status.value,
        stripe_subscription_id=sub.stripe_subscription_id,
        current_period_end=sub.current_period_end.isoformat() if sub.current_period_end else None,
        cancel_at_period_end=sub.cancel_at_period_end,
    )
    return create_response(RESPONSE_STATUS_SUCCESS, "Subscription retrieved", data.model_dump())


@router.post("/checkout")
async def create_checkout(
    body: CheckoutSessionRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    body = body or CheckoutSessionRequest()
    repo = SubscriptionRepository(db)
    sub = await repo.get_by_user_id(current_user.id)
    if sub and subscription_has_pro_access(sub):
        return create_response(
            RESPONSE_STATUS_ERROR,
            "You already have an active Pro subscription. Manage it in the billing portal.",
            None,
        )
    try:
        session = await create_pro_checkout_session(
            current_user,
            success_path=body.success_path,
            cancel_path=body.cancel_path,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
    except Exception as e:
        logger.exception("Stripe checkout failed")
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return create_response(
        RESPONSE_STATUS_SUCCESS,
        "Checkout session created",
        {"id": session["id"], "url": session["url"]},
    )


@router.get("/checkout/status")
async def checkout_status(session_id: str = Query(..., description="Stripe Checkout session ID")):
    if not session_id.strip():
        return JSONResponse(
            content=create_response(RESPONSE_STATUS_ERROR, "Session ID is required.", None),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        sess = await retrieve_checkout_session(session_id)
    except Exception as e:
        logger.warning("Stripe session retrieve failed: %s", e)
        return JSONResponse(
            content=create_response(RESPONSE_STATUS_ERROR, str(e), None),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    ps = getattr(sess, "payment_status", None)
    if ps is None and isinstance(sess, dict):
        ps = sess.get("payment_status")
    if ps == "paid":
        return JSONResponse(
            content=create_response(RESPONSE_STATUS_SUCCESS, "Payment successful", None),
            status_code=status.HTTP_200_OK,
        )
    if ps == "no_payment_required":
        return JSONResponse(
            content=create_response(RESPONSE_STATUS_SUCCESS, "No payment required", None),
            status_code=status.HTTP_200_OK,
        )
    if ps == "unpaid":
        return JSONResponse(
            content=create_response(RESPONSE_STATUS_ERROR, "Payment unpaid or pending", None),
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
        )
    return JSONResponse(
        content=create_response(RESPONSE_STATUS_ERROR, "Unknown payment status", None),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
