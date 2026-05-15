from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class CompetitorAnalysisMode(str, Enum):
    """Crawl mode for competitor analysis"""
    QUICK = "QUICK"
    SITEMAP_ONLY = "SITEMAP_ONLY"
    FULL_CRAWL = "FULL_CRAWL"


class CompetitorAnalysisStatus(str, Enum):
    """Status of competitor analysis"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CompetitorAnalysisWinner(str, Enum):
    """Winner of the comparison"""
    USER = "user"
    COMPETITOR = "competitor"
    TIE = "tie"


class CompetitorAnalysisRequest(BaseModel):
    """Request to analyze competitors"""
    user_url: HttpUrl = Field(..., description="Your website URL")
    competitor_url: HttpUrl = Field(..., description="Competitor website URL")
    mode: CompetitorAnalysisMode = Field(
        default=CompetitorAnalysisMode.QUICK,
        description="Analysis mode: QUICK (homepage only), SITEMAP_ONLY, or FULL_CRAWL"
    )


class MetricComparison(BaseModel):
    """Comparison of a single metric"""
    user_value: Any
    competitor_value: Any
    winner: str  # "user", "competitor", "tie"
    gap: Optional[str] = None
    gap_percentage: Optional[float] = None


class CategoryScore(BaseModel):
    """Score for a category"""
    user: int
    competitor: int


class PerformanceMetrics(BaseModel):
    """Performance-related metrics"""
    category_score: CategoryScore
    load_time: Optional[MetricComparison] = None
    page_size: Optional[MetricComparison] = None
    requests_count: Optional[MetricComparison] = None
    core_web_vitals: Optional[Dict[str, MetricComparison]] = None


class SeoMetrics(BaseModel):
    """SEO-related metrics"""
    category_score: CategoryScore
    title_optimization: Optional[MetricComparison] = None
    meta_description_coverage: Optional[MetricComparison] = None
    heading_structure: Optional[MetricComparison] = None
    image_alt_coverage: Optional[MetricComparison] = None
    canonical_usage: Optional[MetricComparison] = None
    schema_markup: Optional[MetricComparison] = None


class TechnicalMetrics(BaseModel):
    """Technical SEO metrics"""
    category_score: CategoryScore
    https_security: Optional[MetricComparison] = None
    mobile_friendly: Optional[MetricComparison] = None
    robots_txt: Optional[MetricComparison] = None
    sitemap: Optional[MetricComparison] = None
    open_graph: Optional[MetricComparison] = None


class DetailedComparison(BaseModel):
    """Detailed comparison across all categories"""
    performance: Optional[PerformanceMetrics] = None
    seo: Optional[SeoMetrics] = None
    technical: Optional[TechnicalMetrics] = None


class ComparisonSummary(BaseModel):
    """Summary of the comparison"""
    headline: str
    key_insight: str
    encouragement: Optional[str] = None


class StrengthItem(BaseModel):
    """Area where user is winning"""
    category: str
    metric: str
    your_value: str
    competitor_value: str
    advantage: str
    what_this_means: str
    business_impact: Optional[str] = None
    keep_doing: Optional[str] = None


class WeaknessItem(BaseModel):
    """Area where user is losing"""
    category: str
    metric: str
    your_value: str
    competitor_value: str
    gap: str
    what_this_means: str
    business_impact: Optional[str] = None
    improvement_priority: str


class TieItem(BaseModel):
    """Area where both are equal"""
    category: str
    metric: str
    status: str
    note: Optional[str] = None


class ComparisonMatrix(BaseModel):
    """Complete comparison matrix"""
    where_you_win: List[StrengthItem] = Field(default_factory=list)
    where_you_lose: List[WeaknessItem] = Field(default_factory=list)
    tie: List[TieItem] = Field(default_factory=list)


class Suggestion(BaseModel):
    """Business-friendly improvement suggestion"""
    category: str
    priority: str  # "critical", "high", "medium", "low"
    priority_score: int  # 0-100
    issue: str
    your_metric: str
    competitor_metric: str
    what_this_means: str
    what_you_should_do: List[str]
    expected_benefit: str
    timeline: str


class QuickWin(BaseModel):
    """Easy fix with high impact"""
    issue: str
    why_it_matters: str
    effort: str
    effort_level: str  # "easy", "medium", "hard"
    impact: str  # "high", "medium", "low"
    how_to_fix: str
    expected_result: str


class AnalysisMeta(BaseModel):
    """Metadata about the analysis"""
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    pages_analyzed: Dict[str, int]


class OverallScores(BaseModel):
    """Overall scores for both sites"""
    user: int
    competitor: int
    winner: str
    gap: int
    interpretation: str


class CompetitorAnalysisResponse(BaseModel):
    """Complete competitor analysis response"""
    analysis_id: UUID
    mode: CompetitorAnalysisMode
    status: CompetitorAnalysisStatus
    
    urls: Dict[str, str]
    
    analysis_meta: AnalysisMeta
    
    overall_scores: OverallScores
    
    comparison_summary: ComparisonSummary
    
    detailed_comparison: DetailedComparison
    
    comparison_matrix: ComparisonMatrix
    
    suggestions: List[Suggestion]
    
    quick_wins: List[QuickWin]
    
    strengths_to_maintain: List[StrengthItem]
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class CompetitorAnalysisSummary(BaseModel):
    """Summary for listing analyses"""
    analysis_id: UUID
    user_url: str
    competitor_url: str
    mode: CompetitorAnalysisMode
    status: CompetitorAnalysisStatus
    user_score: Optional[int] = None
    competitor_score: Optional[int] = None
    winner: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CompetitorAnalysisList(BaseModel):
    """List of competitor analyses"""
    total: int
    items: List[CompetitorAnalysisSummary]


# Export schemas
class ExportFormat(str, Enum):
    """Export format options"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
