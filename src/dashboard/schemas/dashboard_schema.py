from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class PerformanceChartItem(BaseModel):
    label: str
    value: float
    color: str


class RecentItem(BaseModel):
    id: str
    title: str
    status: str
    created_at: datetime
    score: Optional[float] = None


class RecentAnalyses(BaseModel):
    seo: List[RecentItem]
    keywords: List[RecentItem]
    rank: List[RecentItem]


class DashboardOverviewResponse(BaseModel):
    seo_score: float
    keywords_tracked: int
    total_analyses: int
    performance_chart: List[PerformanceChartItem]
    recent_analyses: RecentAnalyses
    stats: dict