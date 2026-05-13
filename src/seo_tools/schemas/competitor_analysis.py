from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, HttpUrl

from src.seo_tools.schemas.analyze_site_seo import CrawlMode


class CompetitorAnalysisRequest(BaseModel):
    user_url: HttpUrl
    competitor_url: HttpUrl
    crawl_mode: CrawlMode = CrawlMode.SITEMAP_ONLY
    max_pages: int = 100


class CompetitorSiteAudit(BaseModel):
    """One side of the comparison — same payload shape as saved SEO insight / analyze-site output."""

    target_url: str
    crawl_mode: str
    base_url_checks: dict
    url_results: List[dict] = []
    total_pages: int = 0
    avg_response_time_ms: Optional[float] = None
    score: int = 0


class CompetitorPageSummary(BaseModel):
    url: str
    page_type: str
    title: str = ""
    meta_description: str = ""
    keywords: List[str] = []


class KeywordIntentBuckets(BaseModel):
    informational: List[str] = []
    navigational: List[str] = []
    transactional: List[str] = []
    commercial: List[str] = []


class ContentGapItem(BaseModel):
    topic: str
    example_competitor_urls: List[str] = []


class ComparisonRow(BaseModel):
    feature: str
    user: Optional[Union[int, float, str, bool]] = None
    competitor: Optional[Union[int, float, str, bool]] = None
    winner: Optional[str] = None


class RecommendationItem(BaseModel):
    priority: str
    category: str
    title: str
    details: str


class CompetitorAnalysisResponse(BaseModel):
    """Dashboard payload + full audits for drill-down."""

    user_pages: List[CompetitorPageSummary]
    competitor_pages: List[CompetitorPageSummary]
    content_gaps: List[ContentGapItem]
    keywords_by_intent: KeywordIntentBuckets
    user_seo_score: int
    competitor_seo_score: int
    comparison: List[ComparisonRow]
    recommendations: List[RecommendationItem]
    user_site: CompetitorSiteAudit
    competitor_site: CompetitorSiteAudit
    suggestions: List[str] = []
    errors: Dict[str, str] = {}
