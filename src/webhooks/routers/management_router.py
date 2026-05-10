from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from src.config.logger_config import setup_logger
from src.config.database import get_db_session
from src.auth.auth_service import AuthService
from src.auth.repository.user_repository import UserRepository
from src.webhooks.repository.webhook_repository import (
    APIKeyRepository,
    WebhookConfigRepository,
    DeploymentAnalysisRepository,
)
from src.webhooks.services.webhook_service import WebhookService
from src.webhooks.schemas.webhook_schemas import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreateResponse,
    WebhookConfigCreate,
    WebhookConfigResponse,
    WebhookConfigUpdate,
    DeploymentAnalysisResponse,
    DeploymentAnalysisListResponse,
)
from src.core.security import get_current_user
from src.models.user import User
from src.models.cicd_integration import APIKey, WebhookConfig, DeploymentAnalysis

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["CI/CD Management"])


# API Key Management
@router.post("/api-keys", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: APIKeyCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create a new API key for CI/CD integration

    Returns the API key (shown only once). Store it securely!
    """
    try:
        # Generate API key
        service = WebhookService()
        api_key, key_hash = service.generate_api_key()

        async with get_db_session() as db:
            repo = APIKeyRepository(db)

            key_obj = APIKey(
                user_id=current_user.id,
                key_hash=key_hash,
                name=request.name,
                expires_at=request.expires_at,
                is_active=True,
            )
            await repo.create(key_obj)

            # Return response with the actual key (only shown once)
            return APIKeyCreateResponse(
                id=key_obj.id,
                user_id=key_obj.user_id,
                name=key_obj.name,
                is_active=key_obj.is_active,
                created_at=key_obj.created_at,
                last_used_at=key_obj.last_used_at,
                expires_at=key_obj.expires_at,
                api_key=api_key,  # Only shown on creation
                message="Store this API key securely. It will not be shown again!"
            )

    except Exception as e:
        logger.error(f"Error creating API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List all API keys for the current user (without the actual key values)"""
    try:
        async with get_db_session() as db:
            repo = APIKeyRepository(db)
            keys = await repo.get_by_user_id(current_user.id, skip=skip, limit=limit)
            return [APIKeyResponse.model_validate(k) for k in keys]
    except Exception as e:
        logger.error(f"Error listing API keys: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Revoke (deactivate) an API key"""
    try:
        async with get_db_session() as db:
            repo = APIKeyRepository(db)
            key = await repo.get_by_id(key_id)

            if not key or key.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found"
                )

            await repo.deactivate(key_id)
            return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )


# Webhook Config Management
@router.post("/webhook-configs", response_model=WebhookConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook_config(
    request: WebhookConfigCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new webhook configuration"""
    try:
        from src.models.cicd_integration import WebhookProvider

        async with get_db_session() as db:
            repo = WebhookConfigRepository(db)

            # Check if config already exists for this repo
            existing = await repo.get_by_repository(
                current_user.id,
                request.provider,
                request.repository_name
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Webhook config already exists for this repository"
                )

            config = WebhookConfig(
                user_id=current_user.id,
                provider=WebhookProvider(request.provider),
                repository_name=request.repository_name,
                repository_owner=request.repository_owner,
                target_url=str(request.target_url),
                crawl_mode=request.crawl_mode,
                events=request.events,
                is_active=request.is_active,
            )
            await repo.create(config)
            return WebhookConfigResponse.model_validate(config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating webhook config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create webhook config"
        )


@router.get("/webhook-configs", response_model=List[WebhookConfigResponse])
async def list_webhook_configs(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List all webhook configs for the current user"""
    try:
        async with get_db_session() as db:
            repo = WebhookConfigRepository(db)
            configs = await repo.get_by_user_id(current_user.id, skip=skip, limit=limit)
            return [WebhookConfigResponse.model_validate(c) for c in configs]
    except Exception as e:
        logger.error(f"Error listing webhook configs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list webhook configs"
        )


@router.put("/webhook-configs/{config_id}", response_model=WebhookConfigResponse)
async def update_webhook_config(
    config_id: UUID,
    request: WebhookConfigUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a webhook configuration"""
    try:
        async with get_db_session() as db:
            repo = WebhookConfigRepository(db)
            config = await repo.get_by_id(config_id)

            if not config or config.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Webhook config not found"
                )

            updates = {}
            if request.target_url:
                updates["target_url"] = str(request.target_url)
            if request.crawl_mode:
                updates["crawl_mode"] = request.crawl_mode
            if request.events:
                updates["events"] = request.events
            if request.is_active is not None:
                updates["is_active"] = request.is_active

            updated = await repo.update(config_id, **updates)
            return WebhookConfigResponse.model_validate(updated)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating webhook config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update webhook config"
        )


@router.delete("/webhook-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_config(
    config_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Delete a webhook configuration"""
    try:
        async with get_db_session() as db:
            repo = WebhookConfigRepository(db)
            config = await repo.get_by_id(config_id)

            if not config or config.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Webhook config not found"
                )

            await repo.delete(config_id)
            return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webhook config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete webhook config"
        )


# Deployment Analysis History
@router.get("/deployment-analyses", response_model=DeploymentAnalysisListResponse)
async def list_deployment_analyses(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List all deployment analyses for the current user"""
    try:
        async with get_db_session() as db:
            repo = DeploymentAnalysisRepository(db)
            analyses = await repo.get_by_user_id(current_user.id, skip=skip, limit=limit)
            total = len(analyses)  # In production, use a count query

            return DeploymentAnalysisListResponse(
                total=total,
                page=skip // limit + 1 if limit > 0 else 1,
                page_size=limit,
                items=[DeploymentAnalysisResponse.model_validate(a) for a in analyses]
            )
    except Exception as e:
        logger.error(f"Error listing deployment analyses: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list deployment analyses"
        )


@router.get("/deployment-analyses/{analysis_id}", response_model=DeploymentAnalysisResponse)
async def get_deployment_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Get a specific deployment analysis"""
    try:
        async with get_db_session() as db:
            repo = DeploymentAnalysisRepository(db)
            analysis = await repo.get_by_id(analysis_id)

            if not analysis or analysis.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Deployment analysis not found"
                )

            return DeploymentAnalysisResponse.model_validate(analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deployment analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get deployment analysis"
        )
