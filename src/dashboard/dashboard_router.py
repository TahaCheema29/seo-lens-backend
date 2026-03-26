from statistics import mean
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.core.metrics import compute_seo_base_url_checks_metrics
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS
from src.core.security import get_current_user
from src.models.keyword_rank import KeywordRankResult
from src.models.keyword_suggestion import KeywordSuggestion
from src.models.seo_insight import SeoInsightResult
from src.models.user import User
from src.keyword_rank.schemas.keyword_rank import KeywordRankResultResponse
from src.keyword_suggestion.schemas.keyword_suggestion import KeywordSuggestionResponse
from src.seo_insight.schemas.seo_insight import SeoInsightResultResponse


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview")
async def dashboard_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard KPIs and recent analyses."""
    user_id = str(current_user.id)

    # Recent analyses (last 5 for each module)
    seo_rows = await db.execute(
        select(SeoInsightResult)
        .where(SeoInsightResult.user_id == user_id)
        .order_by(SeoInsightResult.created_at.desc())
        .limit(5)
    )
    seo_recent = seo_rows.scalars().all()

    kw_rows = await db.execute(
        select(KeywordSuggestion)
        .where(KeywordSuggestion.user_id == user_id)
        .order_by(KeywordSuggestion.created_at.desc())
        .limit(5)
    )
    kw_recent = kw_rows.scalars().all()

    rank_rows = await db.execute(
        select(KeywordRankResult)
        .where(KeywordRankResult.user_id == user_id)
        .order_by(KeywordRankResult.created_at.desc())
        .limit(5)
    )
    rank_recent = rank_rows.scalars().all()

    # Performance chart (last 10 SEO scores)
    seo_chart_rows = await db.execute(
        select(SeoInsightResult)
        .where(SeoInsightResult.user_id == user_id)
        .order_by(SeoInsightResult.created_at.desc())
        .limit(10)
    )
    seo_chart = seo_chart_rows.scalars().all()

    seo_scores = [compute_seo_base_url_checks_metrics(i.base_url_checks)["score"] for i in seo_chart]
    seo_score = int(round(mean(seo_scores))) if seo_scores else 0

    performance_chart: List[Dict[str, Any]] = [
        {"date": i.created_at, "score": compute_seo_base_url_checks_metrics(i.base_url_checks)["score"]}
        for i in reversed(seo_chart)
    ]

    # Keywords tracked (distinct across suggestion + rank keyword fields)
    suggestion_keywords = await db.execute(
        select(KeywordSuggestion.primary_keyword)
        .where(KeywordSuggestion.user_id == user_id)
    )
    suggestion_keywords_list = suggestion_keywords.scalars().all()

    rank_keywords = await db.execute(
        select(KeywordRankResult.keyword)
        .where(KeywordRankResult.user_id == user_id)
    )
    rank_keywords_list = rank_keywords.scalars().all()

    keywords_tracked = len(set(suggestion_keywords_list + rank_keywords_list))

    # Not currently stored in DB; keep placeholders for dashboard compatibility.
    backlinks = 0
    organic_traffic = "0"

    return create_response(
        status=RESPONSE_STATUS_SUCCESS,
        message="Dashboard overview retrieved successfully",
        data={
            "seoScore": seo_score,
            "keywordsTracked": keywords_tracked,
            "backlinks": backlinks,
            "organicTraffic": organic_traffic,
            "performanceChart": performance_chart,
            "recentAnalyses": {
                "seo": [SeoInsightResultResponse.model_validate(i) for i in seo_recent],
                "keywords": [KeywordSuggestionResponse.model_validate(i) for i in kw_recent],
                "rank": [KeywordRankResultResponse.model_validate(i) for i in rank_recent],
            },
        },
    )

