import enum
from sqlalchemy import Column, String, Boolean, Integer, Text, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from src.config.database import Base
from .base import BaseModel


class WebhookProvider(str, enum.Enum):
    GITHUB = "github"
    GITLAB = "gitlab"


class WebhookEventType(str, enum.Enum):
    """
    Event types that can trigger SEO analysis.
    
    Note: Analysis only triggers on:
    - Merges to main/master/production branches
    - Not on every PR update or random push
    """
    PULL_REQUEST_MERGED = "pull_request_merged"  # PR merged to main/master
    PUSH_TO_PRODUCTION = "push_to_production"     # Push to main/master/production
    MERGE_REQUEST = "merge_request"               # GitLab merge request merged


class WebhookEventStatus(str, enum.Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class APIKey(Base, BaseModel):
    __tablename__ = "api_keys"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key_hash = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey {self.name or self.key_hash[:8]}...>"


class WebhookConfig(Base, BaseModel):
    __tablename__ = "webhook_configs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(Enum(WebhookProvider), nullable=False)
    repository_name = Column(String, nullable=False)
    repository_id = Column(String, nullable=True)
    repository_owner = Column(String, nullable=True)
    webhook_secret = Column(String, nullable=True)
    target_url = Column(String, nullable=False)
    crawl_mode = Column(String, default="standard", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    events = Column(JSON, default=list, nullable=False)

    user = relationship("User", back_populates="webhook_configs")
    events_log = relationship("WebhookEvent", back_populates="config", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WebhookConfig {self.provider}:{self.repository_name}>"


class WebhookEvent(Base, BaseModel):
    __tablename__ = "webhook_events"

    config_id = Column(UUID(as_uuid=True), ForeignKey("webhook_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(Enum(WebhookEventType), nullable=False)
    delivery_id = Column(String, nullable=True, unique=True)
    payload = Column(JSON, nullable=True)
    status = Column(Enum(WebhookEventStatus), default=WebhookEventStatus.RECEIVED, nullable=False)
    error_message = Column(Text, nullable=True)
    source = Column(String, nullable=True)

    config = relationship("WebhookConfig", back_populates="events_log")
    analyses = relationship("DeploymentAnalysis", back_populates="webhook_event", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WebhookEvent {self.event_type}:{self.delivery_id}>"


class DeploymentAnalysis(Base, BaseModel):
    """
    Tracks SEO analysis jobs triggered by deployments to production.
    
    This can be triggered by:
    - PR merged to main/master/production
    - Direct push to main/master/production
    - GitHub Action/manual trigger via API
    
    The pr_number and pr_title fields are optional metadata that help
    track which PR caused the deployment (when applicable).
    """
    __tablename__ = "deployment_analyses"

    webhook_event_id = Column(UUID(as_uuid=True), ForeignKey("webhook_events.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True, index=True)

    # Optional: Track which PR triggered the deployment (if applicable)
    pr_number = Column(Integer, nullable=True)
    pr_title = Column(String, nullable=True)
    
    # Deployment context
    branch_name = Column(String, nullable=True)
    commit_sha = Column(String, nullable=True)
    repository_name = Column(String, nullable=True)
    repository_owner = Column(String, nullable=True)

    # Analysis configuration
    target_url = Column(String, nullable=False)
    crawl_mode = Column(String, default="standard", nullable=False)

    # Analysis results
    seo_insight_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String, default="pending", nullable=False)
    score = Column(Integer, nullable=True)

    # Job tracking
    job_id = Column(String, nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    webhook_event = relationship("WebhookEvent", back_populates="analyses")
    user = relationship("User", back_populates="deployment_analyses")
    api_key = relationship("APIKey")

    def __repr__(self):
        repo = self.repository_name or "unknown"
        return f"<DeploymentAnalysis {repo}:{self.target_url} - {self.status}>"
