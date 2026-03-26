from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


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
    status: str
    created_at: datetime
    
    # Computed fields
    related_keywords_count: Optional[int] = None
    long_tail_keywords_count: Optional[int] = None
    search_results_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class KeywordSuggestionList(BaseModel):
    """Schema for listing keyword suggestions"""
    total: int
    items: List[KeywordSuggestionResponse]


class KeywordSuggestionStatsResponse(BaseModel):
    """Schema for keyword suggestion statistics"""
    total_keywords: int
    completed_count: int
    processing_count: int
    failed_count: int
    pending_count: int
    avg_related_keywords: float
    avg_long_tail_keywords: float


class KeywordSuggestionUpdate(BaseModel):
    """Schema for updating a keyword suggestion"""
    primary_keyword: Optional[str] = None
    related_searches: Optional[List[str]] = None
    people_also_ask: Optional[List[dict]] = None
    status: Optional[str] = None