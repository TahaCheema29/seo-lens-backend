from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime

class AnalyzeKeywordRankRequest(BaseModel):
    url: HttpUrl
    keywords:list[str]

class SearchResult(BaseModel):
    position: int = Field(..., description="Ranking position in Google search results")
    title: str = Field(..., description="Title of the result page")
    url: HttpUrl = Field(..., description="URL of the result page")
    snippet: Optional[str] = Field(None, description="Snippet/description from search results")


class AnalyzeKeywordRankResult(BaseModel):
    keyword: str = Field(..., description="The keyword that was searched")
    target_domain: Optional[str] = Field(None, description="Domain being checked for ranking")
    target_position: Optional[int] = Field(None, description="Position where domain appears in search results")
    total_results: int = Field(..., description="Total results returned from Google CSE API")
    search_results: List[SearchResult] = Field(..., description="List of search result entries")
    timestamp: float = Field(..., description="Unix timestamp when search was done")
    date: datetime = Field(..., description="Readable date and time of search")
