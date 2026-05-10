"""
CI/CD Integration Module for SEO Lens

This module provides:
- GitHub webhook receiver with HMAC signature verification
- GitHub Action trigger endpoint (async pattern)
- API key management for authentication
- Webhook configuration management
- Deployment analysis tracking and history
"""

from .routers import webhook_router, management_router
from .services import WebhookService, WebhookServiceError, InvalidSignatureError, InvalidAPIKeyError
from .schemas import (
    TriggerAnalysisRequest,
    TriggerAnalysisResponse,
    APIKeyCreate,
    APIKeyResponse,
    WebhookConfigCreate,
    WebhookConfigResponse,
    DeploymentAnalysisResponse,
)

__all__ = [
    # Routers
    "webhook_router",
    "management_router",
    # Services
    "WebhookService",
    "WebhookServiceError",
    "InvalidSignatureError",
    "InvalidAPIKeyError",
    # Schemas
    "TriggerAnalysisRequest",
    "TriggerAnalysisResponse",
    "APIKeyCreate",
    "APIKeyResponse",
    "WebhookConfigCreate",
    "WebhookConfigResponse",
    "DeploymentAnalysisResponse",
]
