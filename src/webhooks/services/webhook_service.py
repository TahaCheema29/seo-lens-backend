import hmac
import hashlib
import secrets
import uuid
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from src.config.logger_config import setup_logger
from src.config.database import get_db_session
from src.models.cicd_integration import (
    APIKey,
    WebhookConfig,
    WebhookEvent,
    DeploymentAnalysis,
    WebhookProvider,
    WebhookEventType,
    WebhookEventStatus,
)
from src.webhooks.repository.webhook_repository import (
    APIKeyRepository,
    WebhookConfigRepository,
    WebhookEventRepository,
    DeploymentAnalysisRepository,
)
from src.webhooks.schemas.webhook_schemas import (
    GitHubWebhookPayload,
    TriggerAnalysisRequest,
    TriggerAnalysisResponse,
)
from .job_queue import job_queue


logger = setup_logger(__name__)


class WebhookServiceError(Exception):
    """Base exception for webhook service errors"""
    pass


class InvalidSignatureError(WebhookServiceError):
    """Raised when webhook signature is invalid"""
    pass


class InvalidAPIKeyError(WebhookServiceError):
    """Raised when API key is invalid or expired"""
    pass


class WebhookService:
    """Service for handling webhooks and CI/CD integrations"""

    def __init__(self):
        self.logger = logger

    @staticmethod
    def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
        """
        Verify GitHub webhook signature using HMAC SHA-256

        Args:
            payload: Raw request body bytes
            signature: X-Hub-Signature-256 header value (sha256=<hash>)
            secret: Webhook secret configured in GitHub

        Returns:
            True if signature is valid, False otherwise
        """
        if not signature or not secret:
            return False

        # GitHub signature format: sha256=<hash>
        if not signature.startswith("sha256="):
            return False

        expected_signature = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected_signature}", signature)

    @staticmethod
    def generate_api_key() -> Tuple[str, str]:
        """
        Generate a new API key and its hash

        Returns:
            Tuple of (api_key, key_hash)
        """
        # Generate a secure random API key
        api_key = f"sl_{secrets.token_urlsafe(32)}"
        key_hash = APIKeyRepository.hash_key(api_key)
        return api_key, key_hash

    async def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """
        Validate an API key and check if it's active and not expired

        Args:
            api_key: The API key to validate

        Returns:
            APIKey object if valid, None otherwise

        Raises:
            InvalidAPIKeyError: If key is invalid, inactive, or expired
        """
        if not api_key or not api_key.startswith("sl_"):
            raise InvalidAPIKeyError("Invalid API key format")

        key_hash = APIKeyRepository.hash_key(api_key)

        async with get_db_session() as db:
            repo = APIKeyRepository(db)
            key_obj = await repo.get_by_key_hash(key_hash)

            if not key_obj:
                raise InvalidAPIKeyError("API key not found")

            if not key_obj.is_active:
                raise InvalidAPIKeyError("API key is deactivated")

            if key_obj.expires_at and key_obj.expires_at < datetime.utcnow():
                raise InvalidAPIKeyError("API key has expired")

            # Update last used timestamp
            await repo.update_last_used(key_obj.id)

            return key_obj

    async def process_github_webhook(
        self,
        payload: dict,
        signature: str,
        event_type: str,
        delivery_id: str
    ) -> Optional[str]:
        """
        Process incoming GitHub webhook
        
        Only triggers analysis when:
        1. Code is merged to main/master/production branch
        2. NOT on every PR update or random push

        Args:
            payload: Parsed webhook payload
            signature: X-Hub-Signature-256 header
            event_type: X-GitHub-Event header
            delivery_id: X-GitHub-Delivery header

        Returns:
            Job ID if analysis queued, None otherwise
        """
        try:
            # Parse payload
            webhook_payload = GitHubWebhookPayload(**payload)

            # Extract repository info
            if not webhook_payload.repository:
                self.logger.warning("No repository info in webhook payload")
                return None

            repo_full_name = webhook_payload.repository.full_name
            repo_owner = webhook_payload.repository.owner.get("login") if webhook_payload.repository.owner else None
            repo_name = webhook_payload.repository.name

            # Determine if we should trigger analysis
            should_trigger = False
            trigger_reason = ""
            branch_name = None
            pr_number = None

            # Handle Pull Request events
            if event_type == "pull_request":
                # Only trigger when PR is MERGED (not just opened/updated)
                if webhook_payload.action == "closed" and webhook_payload.pull_request.get("merged") == True:
                    # Check if merged to main/master/production
                    base_branch = webhook_payload.pull_request.get("base", {}).get("ref", "")
                    if base_branch in ["main", "master", "production"]:
                        should_trigger = True
                        trigger_reason = f"PR merged to {base_branch}"
                        branch_name = base_branch
                        pr_number = webhook_payload.pull_request.get("number")
                        self.logger.info(f"PR #{pr_number} merged to {base_branch} in {repo_full_name}")
                    else:
                        self.logger.info(f"PR merged to {base_branch}, not main/master/production - ignoring")
                else:
                    self.logger.info(f"Ignoring PR action: {webhook_payload.action} (only triggers on merge to main/master)")
                    return None

            # Handle Push events
            elif event_type == "push":
                # Only trigger on pushes to main/master/production branches
                ref = payload.get("ref", "")
                branch_name = ref.replace("refs/heads/", "")
                
                if branch_name in ["main", "master", "production"]:
                    # Check if this is a merge commit (has multiple parents)
                    # or if files affecting the website changed
                    commits = payload.get("commits", [])
                    
                    # For now, trigger on any push to main/master
                    # TODO: Add logic to detect if website-related files actually changed
                    should_trigger = True
                    trigger_reason = f"Push to {branch_name}"
                    self.logger.info(f"Push to {branch_name} in {repo_full_name}")
                else:
                    self.logger.info(f"Push to {branch_name}, not main/master/production - ignoring")
                    return None
            
            else:
                self.logger.info(f"Ignoring event type: {event_type}")
                return None

            if not should_trigger:
                return None

            # Find webhook config and trigger analysis
            async with get_db_session() as db:
                config_repo = WebhookConfigRepository(db)

                # Log the event with appropriate type
                event_repo = WebhookEventRepository(db)
                
                # Determine event type based on what triggered it
                if event_type == "pull_request":
                    event_type_enum = WebhookEventType.PULL_REQUEST_MERGED
                elif event_type == "push":
                    event_type_enum = WebhookEventType.PUSH_TO_PRODUCTION
                else:
                    event_type_enum = WebhookEventType.MERGE_REQUEST
                
                event = WebhookEvent(
                    config_id=None,  # Will be set if config found
                    event_type=event_type_enum,
                    delivery_id=delivery_id,
                    payload=payload,
                    status=WebhookEventStatus.RECEIVED,
                    source="github_webhook"
                )
                await event_repo.create(event)

                # TODO: Find matching config and verify signature
                # Then trigger analysis
                self.logger.info(f"Would trigger analysis for {repo_full_name}: {trigger_reason}")
                return None

        except Exception as e:
            self.logger.error(f"Error processing GitHub webhook: {e}", exc_info=True)
            return None

    async def trigger_analysis_from_action(
        self,
        request: TriggerAnalysisRequest,
        api_key_str: str
    ) -> TriggerAnalysisResponse:
        """
        Trigger SEO analysis from GitHub Action

        This is the main entry point for the async pattern:
        1. Validate API key
        2. Create deployment analysis record
        3. Queue job for async processing
        4. Return immediately with job ID

        Args:
            request: Analysis request from GitHub Action
            api_key_str: API key for authentication

        Returns:
            TriggerAnalysisResponse with job ID
        """
        try:
            # Validate API key
            api_key_obj = await self.validate_api_key(api_key_str)

            # Create analysis record
            async with get_db_session() as db:
                analysis_repo = DeploymentAnalysisRepository(db)

                analysis = DeploymentAnalysis(
                    id=uuid.uuid4(),
                    user_id=api_key_obj.user_id,
                    api_key_id=api_key_obj.id,
                    pr_number=request.pr_number,
                    pr_title=None,  # Will be updated when processing
                    branch_name=request.branch,
                    commit_sha=request.commit_sha,
                    repository_name=request.repository,
                    repository_owner=request.owner,
                    target_url=str(request.url),
                    crawl_mode=request.crawl_mode,
                    status="queued",
                    job_id=str(uuid.uuid4())
                )

                await analysis_repo.create(analysis)

                # Enqueue job for async processing
                # Email will be fetched from user record in job_queue if not provided
                queued = await job_queue.enqueue(
                    job_id=analysis.job_id,
                    analysis_id=analysis.id,
                    user_id=api_key_obj.user_id,
                    target_url=str(request.url),
                    crawl_mode=request.crawl_mode,
                    email=request.email  # Don't try to access api_key_obj.user.email here
                )

                if not queued:
                    # Update analysis status to failed if queueing failed
                    await analysis_repo.update_status(analysis.id, "failed")
                    raise WebhookServiceError("Failed to enqueue analysis job")

                self.logger.info(
                    f"Queued analysis job {analysis.job_id} for user {api_key_obj.user_id}, "
                    f"URL: {request.url}"
                )

                return TriggerAnalysisResponse(
                    job_id=analysis.job_id,
                    status="queued",
                    message="Analysis queued successfully. You will receive an email when complete.",
                    estimated_time_seconds=120  # ~2 minutes for analysis
                )

        except InvalidAPIKeyError as e:
            self.logger.warning(f"Invalid API key attempt: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error triggering analysis: {e}", exc_info=True)
            raise WebhookServiceError(f"Failed to trigger analysis: {str(e)}")

    async def get_job_status(self, job_id: str) -> dict:
        """
        Get the status of a job

        Args:
            job_id: The job ID to check

        Returns:
            Dict with job status information
        """
        async with get_db_session() as db:
            analysis_repo = DeploymentAnalysisRepository(db)
            analysis = await analysis_repo.get_by_job_id(job_id)

            if not analysis:
                return {
                    "job_id": job_id,
                    "status": "not_found",
                    "error": "Job not found"
                }

            return {
                "job_id": job_id,
                "status": analysis.status,
                "score": analysis.score,
                "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
            }
