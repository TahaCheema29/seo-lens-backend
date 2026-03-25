from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime


class SearchResult(BaseModel):
    position: int = Field(..., description="Ranking position in Google search results")
    title: str = Field(..., description="Title of the result page")
    url: HttpUrl = Field(..., description="URL of the result page")
    snippet: Optional[str] = Field(None, description="Snippet/description from search results")


class PeopleAlsoAskItem(BaseModel):
    question: str = Field(..., description="A 'People Also Ask' question")
    keyword: str = Field(..., description="Keyword this question is related to")


class SuggestKeywordResult(BaseModel):
    primary_keyword: str = Field(..., description="The main keyword researched")
    search_results: List[SearchResult] = Field(default_factory=list, description="List of search results from Google CSE or fallback sources")
    related_searches: List[str] = Field(default_factory=list, description="Related searches found on Google or generated heuristically")
    people_also_ask: List[PeopleAlsoAskItem] = Field(default_factory=list, description="'People also ask' questions related to the keyword")
    autocomplete_suggestions: List[str] = Field(default_factory=list, description="Autocomplete suggestions from Google search box or related sources")
    long_tail_keywords: List[str] = Field(default_factory=list, description="Long-tail keyword phrases discovered from search results or generated heuristics")
    total_related_terms: int = Field(..., description="Total count of related terms discovered")
    timestamp: float = Field(..., description="Unix timestamp when research was performed")
    date: datetime = Field(..., description="Human-readable datetime when research was performed")


class SuggestKeywordRequest(BaseModel):
    keywords: List[str] = Field(..., description="List of keywords to research")
