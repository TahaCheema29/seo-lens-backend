"""
Subscription Router
API endpoints for subscription management
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.payments.subscription_repository import SubscriptionRepository
from src.payments.subscription_service import SubscriptionService
from src.core.response_helper import create_response

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_subscription_service(db: AsyncSession = Depends(get_db)) -> SubscriptionService:
    """Dependency to get subscription service"""
    return SubscriptionService(db)


@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Get current user's subscription status
    
    Returns subscription tier, status, and Pro access information
    """
    subscription_status = await service.get_subscription_status(current_user.id)
    return create_response(
        True,
        "Subscription retrieved successfully",
        subscription_status
    )


@router.post("/subscription/checkout")
async def create_checkout_session(
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Create Stripe checkout session for Pro subscription
    
    Returns checkout URL to redirect user to Stripe payment page
    """
    try:
        # Check if user already has Pro
        subscription = await service.get_subscription(current_user.id)
        if subscription.is_pro:
            return create_response(
                False,
                "You already have a Pro subscription",
                {"tier": "pro"}
            )
        
        # Create checkout session
        checkout_data = await service.create_checkout_session(
            user_id=current_user.id,
            user_email=current_user.email,
        )
        
        return create_response(
            True,
            "Checkout session created",
            checkout_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.get("/payment/success", response_class=HTMLResponse)
async def payment_success_page(
    request: Request,
    session_id: Optional[str] = None,
):
    """
    Payment success page
    
    Displayed after successful Stripe checkout
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Successful - SEO Lens</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                text-align: center;
                background: white;
                padding: 3rem;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 500px;
                margin: 20px;
            }}
            .icon {{
                width: 80px;
                height: 80px;
                background: #48bb78;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1.5rem;
            }}
            .icon svg {{
                width: 40px;
                height: 40px;
                fill: white;
            }}
            h1 {{
                color: #2d3748;
                margin-bottom: 1rem;
                font-size: 2rem;
            }}
            p {{
                color: #718096;
                margin-bottom: 2rem;
                line-height: 1.6;
            }}
            .btn {{
                background: #667eea;
                color: white;
                padding: 1rem 2rem;
                border-radius: 8px;
                text-decoration: none;
                display: inline-block;
                font-weight: 600;
                transition: background 0.3s;
            }}
            .btn:hover {{
                background: #5a67d8;
            }}
            .features {{
                text-align: left;
                background: #f7fafc;
                padding: 1.5rem;
                border-radius: 10px;
                margin: 1.5rem 0;
            }}
            .features h3 {{
                margin-top: 0;
                color: #2d3748;
            }}
            .features ul {{
                list-style: none;
                padding: 0;
            }}
            .features li {{
                padding: 0.5rem 0;
                color: #4a5568;
            }}
            .features li:before {{
                content: "✓";
                color: #48bb78;
                font-weight: bold;
                margin-right: 0.5rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">
                <svg viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
            </div>
            <h1>Payment Successful!</h1>
            <p>Welcome to SEO Lens Pro! Your payment has been processed successfully and you now have access to all premium features.</p>
            
            <div class="features">
                <h3>Your Pro Features:</h3>
                <ul>
                    <li>Competitor Analysis</li>
                    <li>CI/CD Auto Re-analysis</li>
                    <li>Advanced SEO Insights</li>
                    <li>Priority Support</li>
                </ul>
            </div>
            
            <a href="{request.base_url}" class="btn">Go to Dashboard</a>
        </div>
    </body>
    </html>
    """
    return html_content


@router.get("/payment/cancel", response_class=HTMLResponse)
async def payment_cancel_page(request: Request):
    """
    Payment cancel page
    
    Displayed when user cancels Stripe checkout
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Cancelled - SEO Lens</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            }}
            .container {{
                text-align: center;
                background: white;
                padding: 3rem;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.1);
                max-width: 500px;
                margin: 20px;
            }}
            .icon {{
                width: 80px;
                height: 80px;
                background: #ed8936;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1.5rem;
            }}
            .icon svg {{
                width: 40px;
                height: 40px;
                fill: white;
            }}
            h1 {{
                color: #2d3748;
                margin-bottom: 1rem;
                font-size: 2rem;
            }}
            p {{
                color: #718096;
                margin-bottom: 2rem;
                line-height: 1.6;
            }}
            .btn {{
                background: #667eea;
                color: white;
                padding: 1rem 2rem;
                border-radius: 8px;
                text-decoration: none;
                display: inline-block;
                font-weight: 600;
                margin: 0.5rem;
                transition: background 0.3s;
            }}
            .btn:hover {{
                background: #5a67d8;
            }}
            .btn-secondary {{
                background: #e2e8f0;
                color: #4a5568;
            }}
            .btn-secondary:hover {{
                background: #cbd5e0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">
                <svg viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
            </div>
            <h1>Payment Cancelled</h1>
            <p>Your payment was cancelled. You can still use all Standard features for free, or try upgrading to Pro again whenever you're ready.</p>
            
            <div>
                <a href="{request.base_url}" class="btn">Go to Dashboard</a>
                <a href="{request.base_url}payments/subscription/checkout" class="btn btn-secondary">Try Again</a>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content
