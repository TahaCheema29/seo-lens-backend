from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


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
    created_at: datetime
    
    class Config:
        from_attributes = True


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