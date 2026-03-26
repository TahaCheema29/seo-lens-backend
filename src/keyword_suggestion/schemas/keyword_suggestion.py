from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from src.core.metrics import compute_keyword_suggestion_metrics, infer_result_status


class KeywordSuggestionCreate(BaseModel):
    """Schema for creating a keyword suggestion record"""
    primary_keyword: str
    search_results: List[dict] = Field(default_factory=list)
    related_searches: List[str] = Field(default_factory=list)
    people_also_ask: List[dict] = Field(default_factory=list)
    autocomplete_suggestions: List[str] = Field(default_factory=list)
    long_tail_keywords: List[str] = Field(default_factory=list)
    total_related_terms: int = 0
    timestamp: float
    date: str


class KeywordSuggestionResponse(BaseModel):
    """Schema for reading a keyword suggestion"""
    id: UUID
    user_id: UUID
    primary_keyword: str
    search_results: List[dict]
    related_searches: List[str]
    people_also_ask: List[dict]
    autocomplete_suggestions: List[str]
    long_tail_keywords: List[str]
    total_related_terms: int
    timestamp: float
    date: str
    status: str = "completed"
    created_at: datetime

    # Computed fields (required by FE/dashboard)
    relatedKeywordsCount: int = 0
    longTailKeywordsCount: int = 0
    searchResultsCount: int = 0
    
    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def _compute_metrics(self) -> "KeywordSuggestionResponse":
        counts = compute_keyword_suggestion_metrics(
            related_searches=self.related_searches,
            long_tail_keywords=self.long_tail_keywords,
            search_results=self.search_results,
        )
        self.relatedKeywordsCount = counts["relatedKeywordsCount"]
        self.longTailKeywordsCount = counts["longTailKeywordsCount"]
        self.searchResultsCount = counts["searchResultsCount"]
        self.status = infer_result_status(self.status, fallback="completed")
        return self


class KeywordSuggestionList(BaseModel):
    """Schema for listing keyword suggestions"""
    total: int
    items: List[KeywordSuggestionResponse]


class KeywordSuggestionUpdate(BaseModel):
    """Schema for updating a keyword suggestion"""
    primary_keyword: Optional[str] = None
    related_searches: Optional[List[str]] = None
    people_also_ask: Optional[List[dict]] = None