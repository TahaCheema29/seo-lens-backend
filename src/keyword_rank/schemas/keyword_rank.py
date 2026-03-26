from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class KeywordRankResultCreate(BaseModel):
    """Schema for creating a keyword rank result record"""
    target_url: str
    keywords: List[str]
    keyword: str
    target_domain: Optional[str] = None
    target_position: Optional[int] = None
    total_results: int
    search_results: List[dict]
    timestamp: float
    date: str


class KeywordRankResultResponse(BaseModel):
    """Schema for reading a keyword rank result"""
    id: UUID
    user_id: UUID
    target_url: str
    keywords: List[str]
    keyword: str
    target_domain: Optional[str]
    target_position: Optional[int]
    total_results: int
    search_results: List[dict]
    timestamp: float
    date: str
    status: str
    created_at: datetime
    
    # Computed fields
    domain: Optional[str] = None
    top_10_count: Optional[int] = None
    not_ranking_count: Optional[int] = None
    avg_position: Optional[float] = None
    
    class Config:
        from_attributes = True


class KeywordRankResultList(BaseModel):
    """Schema for listing keyword rank results"""
    total: int
    items: List[KeywordRankResultResponse]


class KeywordRankStatsResponse(BaseModel):
    """Schema for keyword rank statistics"""
    total_keywords: int
    top_10_count: int
    avg_position: float
    completed_count: int
    processing_count: int
    failed_count: int
    pending_count: int


class KeywordRankResultUpdate(BaseModel):
    """Schema for updating a keyword rank result"""
    target_url: Optional[str] = None
    keywords: Optional[List[str]] = None
    status: Optional[str] = None