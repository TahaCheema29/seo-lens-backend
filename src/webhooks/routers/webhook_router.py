from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.config.logger_config import setup_logger
from src.config.redis_client import redis_client
from src.config.database import get_db
from src.webhooks.services.webhook_service import WebhookService, InvalidAPIKeyError, WebhookServiceError
from src.webhooks.schemas.webhook_schemas import (
    TriggerAnalysisRequest,
    TriggerAnalysisResponse,
    JobStatusResponse,
)
from src.payments.subscription_service import SubscriptionService

logger = setup_logger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
security = HTTPBearer(auto_error=False)

# Initialize rate limiter with Redis storage
limiter = Limiter(key_func=get_remote_address)


class APIKeyRateLimitExceeded(Exception):
    """Raised when API key rate limit is exceeded"""
    pass


async def check_api_key_rate_limit(api_key: str) -> bool:
    """
    Check if API key has exceeded rate limit
    
    Limits: 100 requests per hour per API key
    
    Args:
        api_key: The API key to check
        
    Returns:
        True if within limit, raises exception if exceeded
    """
    from src.webhooks.repository.webhook_repository import APIKeyRepository
    
    key_hash = APIKeyRepository.hash_key(api_key)
    rate_limit_key = f"rate_limit:{key_hash}"
    
    try:
        # Increment counter
        request_count = await redis_client.incr(rate_limit_key)
        
        # Set expiry on first request
        if request_count == 1:
            await redis_client.expire(rate_limit_key, 3600)  # 1 hour
        
        # Check limit (100 requests per hour)
        if request_count > 100:
            logger.warning(f"API key rate limit exceeded for hash: {key_hash[:8]}...")
            raise APIKeyRateLimitExceeded(
                f"Rate limit exceeded: 100 requests per hour. "
                f"Current count: {request_count}"
            )
        
        return True
        
    except APIKeyRateLimitExceeded:
        raise
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        # Fail open - allow request if we can't check rate limit
        return True


@router.post("/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: Optional[str] = Header(None),
    x_github_delivery: Optional[str] = Header(None),
):
    """
    Receive GitHub webhook events

    This endpoint receives webhook events from GitHub when:
    - Pull requests are opened/updated
    - Code is pushed to main branch

    The webhook must be configured with a secret for signature verification.
    """
    try:
        # Read raw payload for signature verification
        body = await request.body()

        # Parse JSON payload
        payload = await request.json()

        service = WebhookService()
        job_id = await service.process_github_webhook(
            payload=payload,
            signature=x_hub_signature_256,
            event_type=x_github_event,
            delivery_id=x_github_delivery
        )

        if job_id:
            return {"status": "accepted", "job_id": job_id}
        else:
            return {"status": "accepted", "message": "Event received but no action taken"}

    except Exception as e:
        logger.error(f"Error processing GitHub webhook: {e}", exc_info=True)
        # Return 202 anyway to prevent GitHub from retrying
        return {"status": "accepted", "message": "Event received"}


@router.post("/trigger", response_model=TriggerAnalysisResponse)
@limiter.limit("30/minute")  # IP-based: 30 requests per minute per IP
async def trigger_analysis(
    request: Request,  # Must be named 'request' for slowapi - Starlette Request
    analysis_data: TriggerAnalysisRequest,  # Renamed to avoid conflict with 'request'
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """
    Trigger SEO analysis from GitHub Action (Async Pattern)

    This is the primary endpoint for CI/CD integration. It:
    1. Validates the API key
    2. Creates a PR analysis record
    3. Queues the job for async processing
    4. Returns immediately with a job ID (15-20 seconds)

    Rate Limits:
    - 30 requests per minute per IP address
    - 100 requests per hour per API key

    The actual SEO analysis runs asynchronously and results are emailed
    to the user when complete.

    **Authentication**: Bearer token with API key
    **Example**:
    ```bash
    curl -X POST https://api.seo-lens.com/webhooks/trigger \
      -H "Authorization: Bearer sl_your_api_key" \
      -H "Content-Type: application/json" \
      -d '{
        "url": "https://example.com",
        "crawl_mode": "standard",
        "repository": "my-repo",
        "owner": "my-org",
        "pr_number": 123,
        "branch": "feature-branch",
        "commit_sha": "abc123"
      }'
    ```
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide it in the Authorization header as 'Bearer <api_key>'"
        )

    api_key = credentials.credentials

    try:
        # Check API key rate limit (100/hour per key)
        await check_api_key_rate_limit(api_key)
        
        # Get database session for subscription check
        db_gen = get_db()
        db = await db_gen.asend(None)
        
        try:
            # Validate API key and get user info
            webhook_service = WebhookService()
            api_key_obj = await webhook_service.validate_api_key(api_key)
            
            # Check if user has Pro subscription
            subscription_service = SubscriptionService(db)
            is_pro = await subscription_service.is_pro_user(api_key_obj.user_id)
            
            if not is_pro:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "status": False,
                        "message": "CI/CD auto re-analysis requires a Pro subscription",
                        "data": {
                            "current_tier": "standard",
                            "required_tier": "pro",
                            "upgrade_url": "/api/payments/subscription/checkout"
                        }
                    }
                )
            
            service = WebhookService()
            response = await service.trigger_analysis_from_action(analysis_data, api_key)
            return response
            
        finally:
            await db.close()

    except InvalidAPIKeyError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except APIKeyRateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please slow down your requests."
        )
    except WebhookServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in trigger_analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
@limiter.limit("60/minute")  # IP-based: 60 requests per minute per IP
async def get_job_status(
    job_id: str,
    request: Request,  # Required by slowapi
):
    """
    Get the status of a queued analysis job

    Returns the current status, progress, and results (if complete)
    """
    try:
        service = WebhookService()
        status = await service.get_job_status(job_id)

        return JobStatusResponse(
            job_id=status["job_id"],
            status=status["status"],
            error=status.get("error"),
            score=status.get("score"),
            result_url=f"/pr-analyses/{job_id}" if status["status"] == "completed" else None
        )

    except Exception as e:
        logger.error(f"Error getting job status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job status"
        )
