from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from src.core.metrics import compute_keyword_rank_metrics, infer_result_status


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
    status: str = "completed"
    
    created_at: datetime

    # Computed fields (required by FE/dashboard)
    domain: str = ""
    top10Count: int = 0
    notRankingCount: int = 0
    avgPosition: Optional[float] = None
    
    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def _compute_metrics(self) -> "KeywordRankResultResponse":
        metrics = compute_keyword_rank_metrics(
            target_url=self.target_url,
            target_position=self.target_position,
            search_results=self.search_results,
        )
        self.domain = metrics["domain"]
        self.top10Count = metrics["top10Count"]
        self.notRankingCount = metrics["notRankingCount"]
        self.avgPosition = metrics["avgPosition"]
        self.status = infer_result_status(self.status, fallback="completed")
        return self


class KeywordRankResultList(BaseModel):
    """Schema for listing keyword rank results"""
    total: int
    items: List[KeywordRankResultResponse]


class KeywordRankResultUpdate(BaseModel):
    """Schema for updating a keyword rank result"""
    target_url: Optional[str] = None
    keywords: Optional[List[str]] = None