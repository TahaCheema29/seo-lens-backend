from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from uuid import UUID


class GitHubPullRequest(BaseModel):
    number: int
    title: str
    body: Optional[str] = None
    html_url: str
    head: Dict[str, Any]
    base: Dict[str, Any]
    user: Optional[Dict[str, Any]] = None
    state: str = "open"


class GitHubRepository(BaseModel):
    id: int
    name: str
    full_name: str
    html_url: str
    owner: Dict[str, Any]
    description: Optional[str] = None
    default_branch: str = "main"


class GitHubWebhookPayload(BaseModel):
    action: Optional[str] = None
    number: Optional[int] = None
    pull_request: Optional[GitHubPullRequest] = None
    repository: Optional[GitHubRepository] = None
    ref: Optional[str] = None
    before: Optional[str] = None
    after: Optional[str] = None
    sender: Optional[Dict[str, Any]] = None


class GitHubActionPayload(BaseModel):
    repository: str
    owner: str
    pr_number: Optional[int] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    action: str = "trigger"


class TriggerAnalysisRequest(BaseModel):
    url: HttpUrl = Field(..., description="Target URL to analyze")
    crawl_mode: str = Field(default="standard", description="Crawl mode: standard, deep, light")
    email: Optional[str] = Field(None, description="Email to send results to")
    repository: Optional[str] = Field(None, description="Repository name")
    owner: Optional[str] = Field(None, description="Repository owner")
    pr_number: Optional[int] = Field(None, description="PR number if triggered from PR")
    branch: Optional[str] = Field(None, description="Branch name")
    commit_sha: Optional[str] = Field(None, description="Commit SHA")
    api_key: Optional[str] = Field(None, description="API key for authentication")


class TriggerAnalysisResponse(BaseModel):
    job_id: str
    status: str
    message: str
    estimated_time_seconds: Optional[int] = None


class WebhookConfigCreate(BaseModel):
    provider: str = Field(..., description="Provider: github, gitlab")
    repository_name: str
    repository_owner: Optional[str] = None
    target_url: HttpUrl
    crawl_mode: str = Field(default="standard")
    events: List[str] = Field(default=["pull_request", "push"])
    is_active: bool = Field(default=True)


class WebhookConfigUpdate(BaseModel):
    target_url: Optional[HttpUrl] = None
    crawl_mode: Optional[str] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WebhookConfigResponse(BaseModel):
    id: UUID
    user_id: UUID
    provider: str
    repository_name: str
    repository_owner: Optional[str] = None
    target_url: str
    crawl_mode: str
    events: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreate(BaseModel):
    name: Optional[str] = Field(None, description="Friendly name for the API key")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")


class APIKeyResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: Optional[str]
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    """Response schema for API key creation - includes the actual key (shown only once)"""
    id: UUID
    user_id: UUID
    name: Optional[str]
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    api_key: str  # The actual API key - only shown on creation
    message: str = "Store this API key securely. It will not be shown again!"


class DeploymentAnalysisResponse(BaseModel):
    """Response schema for deployment analysis records"""
    id: UUID
    user_id: UUID
    # Optional PR info (when analysis triggered by PR merge)
    pr_number: Optional[int] = Field(None, description="PR number if triggered by merge")
    pr_title: Optional[str] = Field(None, description="PR title if triggered by merge")
    # Deployment context
    branch_name: Optional[str] = Field(None, description="Branch that was deployed")
    commit_sha: Optional[str] = Field(None, description="Commit SHA")
    repository_name: Optional[str] = Field(None, description="Repository name")
    repository_owner: Optional[str] = Field(None, description="Repository owner")
    # Analysis configuration
    target_url: str = Field(..., description="URL that was analyzed")
    crawl_mode: str = Field(..., description="Crawl mode used")
    # Analysis results
    status: str = Field(..., description="Analysis status: pending, processing, completed, failed")
    score: Optional[int] = Field(None, description="SEO score (0-100)")
    job_id: Optional[str] = Field(None, description="Job ID for tracking")
    # Timestamps
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeploymentAnalysisListResponse(BaseModel):
    """Response schema for listing deployment analyses"""
    total: int
    page: int
    page_size: int
    items: List[DeploymentAnalysisResponse]


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[int] = None
    score: Optional[int] = None
    error: Optional[str] = None
    result_url: Optional[str] = None
