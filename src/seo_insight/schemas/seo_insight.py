from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from src.core.metrics import compute_seo_base_url_checks_metrics, infer_result_status


class SeoInsightResultCreate(BaseModel):
    """Schema for creating an SEO insight result record"""
    target_url: str
    crawl_mode: str
    base_url_checks: dict
    url_results: List[dict] = Field(default_factory=list)
    total_pages: int = 0
    avg_response_time_ms: Optional[float] = None


class SeoInsightResultResponse(BaseModel):
    """Schema for reading an SEO insight result"""
    id: UUID
    user_id: UUID
    target_url: str
    crawl_mode: str
    base_url_checks: dict
    url_results: List[dict]
    total_pages: int
    avg_response_time_ms: Optional[float]
    status: str = "completed"

    # Computed fields (required by FE/dashboard)
    score: int = 0
    criticalIssues: int = 0
    warnings: int = 0
    passedChecks: int = 0
    pageCount: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def _compute_metrics(self) -> "SeoInsightResultResponse":
        metrics = compute_seo_base_url_checks_metrics(self.base_url_checks)
        self.score = metrics["score"]
        self.criticalIssues = metrics["criticalIssues"]
        self.warnings = metrics["warnings"]
        self.passedChecks = metrics["passedChecks"]
        self.pageCount = self.total_pages
        self.status = infer_result_status(self.status, fallback="completed")
        return self


class SeoInsightResultList(BaseModel):
    """Schema for listing SEO insight results"""
    total: int
    items: List[SeoInsightResultResponse]


class SeoInsightResultUpdate(BaseModel):
    """Schema for updating an SEO insight result"""
    target_url: Optional[str] = None
    crawl_mode: Optional[str] = None
    base_url_checks: Optional[dict] = None
    url_results: Optional[List[dict]] = None