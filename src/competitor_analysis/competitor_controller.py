"""
Competitor Analysis Controller
Handles HTTP requests and responses for competitor analysis
"""

from typing import Optional
from fastapi import HTTPException, status
from src.competitor_analysis.competitor_service import CompetitorAnalysisService
from src.competitor_analysis.schemas import (
    CompetitorAnalysisRequest,
    CompetitorAnalysisResponse,
    CompetitorAnalysisList
)
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS, RESPONSE_STATUS_ERROR


class CompetitorAnalysisController:
    """Controller for competitor analysis operations"""
    
    def __init__(self, service: CompetitorAnalysisService):
        self.service = service
    
    async def analyze_competitors(
        self,
        request: CompetitorAnalysisRequest,
        user_id: Optional[str] = None
    ) -> dict:
        """
        Analyze competitors
        
        Args:
            request: Analysis request with URLs and mode
            user_id: Optional user ID for authenticated users
            
        Returns:
            Analysis response
        """
        try:
            result = await self.service.analyze_competitors(
                user_url=str(request.user_url),
                competitor_url=str(request.competitor_url),
                mode=request.mode,
                user_id=user_id
            )
            
            return create_response(
                status=RESPONSE_STATUS_SUCCESS,
                message="Competitor analysis completed successfully",
                data=result
            )
            
        except Exception as e:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message=f"Failed to analyze competitors: {str(e)}",
                data=None
            )
    
    async def get_analysis(self, analysis_id: str, user_id: Optional[str] = None) -> dict:
        """
        Get analysis by ID
        
        Args:
            analysis_id: Analysis ID
            user_id: Optional user ID for ownership check
            
        Returns:
            Analysis data
        """
        try:
            analysis = await self.service.get_analysis_by_id(analysis_id)
            
            if not analysis:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Analysis not found"
                )
            
            # Check ownership if user_id is provided
            if user_id and analysis.user_id and str(analysis.user_id) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to access this analysis"
                )
            
            # Build response from stored data
            # Calculate duration
            duration_seconds = 0.0
            started_at = analysis.created_at.isoformat() if analysis.created_at else None
            completed_at = analysis.completed_at.isoformat() if analysis.completed_at else None
            if analysis.completed_at and analysis.created_at:
                duration_seconds = (analysis.completed_at - analysis.created_at).total_seconds()
            
            # Get pages analyzed from SEO data
            user_pages = 0
            competitor_pages = 0
            user_urls = []
            comp_urls = []
            if analysis.user_seo_data and isinstance(analysis.user_seo_data, dict):
                url_results = analysis.user_seo_data.get("url_results", [])
                user_pages = len(url_results)
                user_urls = [r.get("url", "") for r in url_results if isinstance(r, dict)]
            if analysis.competitor_seo_data and isinstance(analysis.competitor_seo_data, dict):
                url_results = analysis.competitor_seo_data.get("url_results", [])
                competitor_pages = len(url_results)
                comp_urls = [r.get("url", "") for r in url_results if isinstance(r, dict)]
            
            # Build comparison matrix from strengths and weaknesses
            strengths = analysis.strengths or []
            weaknesses = analysis.weaknesses or []
            
            # Generate a simple summary if not available
            comparison_report = analysis.comparison_report or {}
            summary = {
                "headline": f"Your score: {analysis.user_score or 0} vs Competitor: {analysis.competitor_score or 0}",
                "key_insight": f"Score gap: {analysis.score_gap or 0} points",
            }
            if analysis.winner:
                if analysis.winner.value == "user":
                    summary["encouragement"] = "You're ahead! Keep up the good work."
                elif analysis.winner.value == "competitor":
                    summary["encouragement"] = "Room for improvement. Check the suggestions below."
            
            result = {
                "analysis_id": str(analysis.id),
                "mode": analysis.crawl_mode.value,
                "status": analysis.status.value,
                "urls": {
                    "user": analysis.user_url,
                    "competitor": analysis.competitor_url
                },
                "overall_scores": {
                    "user": analysis.user_score or 0,
                    "competitor": analysis.competitor_score or 0,
                    "winner": analysis.winner.value if analysis.winner else None,
                    "gap": analysis.score_gap or 0,
                    "interpretation": summary["headline"]
                },
                "comparison_summary": summary,
                "comparison_matrix": {
                    "where_you_win": strengths,
                    "where_you_lose": weaknesses,
                    "tie": []
                },
                "suggestions": analysis.suggestions or [],
                "quick_wins": analysis.quick_wins or [],
                "strengths_to_maintain": strengths,
                "detailed_comparison": comparison_report,
                "analysis_meta": {
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "duration_seconds": round(duration_seconds, 1),
                    "pages_analyzed": {
                        "user": user_pages,
                        "competitor": competitor_pages
                    },
                    "urls_crawled": {
                        "user": user_urls[:10] if user_urls else [],
                        "competitor": comp_urls[:10] if comp_urls else []
                    }
                },
                "created_at": started_at
            }
            
            return create_response(
                status=RESPONSE_STATUS_SUCCESS,
                message="Analysis retrieved successfully",
                data=result
            )
            
        except HTTPException:
            raise
        except Exception as e:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message=f"Failed to retrieve analysis: {str(e)}",
                data=None
            )
    
    async def get_user_analyses(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> dict:
        """
        Get analyses for authenticated user
        
        Args:
            user_id: User ID
            skip: Number of items to skip
            limit: Number of items to return
            
        Returns:
            List of analyses
        """
        try:
            result = await self.service.get_user_analyses(user_id, skip, limit)
            
            if not result.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get("error", "Failed to retrieve analyses")
                )
            
            return create_response(
                status=RESPONSE_STATUS_SUCCESS,
                message="Analyses retrieved successfully",
                data=result["data"]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message=f"Failed to retrieve analyses: {str(e)}",
                data=None
            )
    
    async def delete_analysis(self, user_id: str, analysis_id: str) -> dict:
        """
        Delete an analysis
        
        Args:
            user_id: User ID
            analysis_id: Analysis ID to delete
            
        Returns:
            Success response
        """
        try:
            deleted = await self.service.delete_analysis(user_id, analysis_id)
            
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Analysis not found or you don't have permission to delete it"
                )
            
            return create_response(
                status=RESPONSE_STATUS_SUCCESS,
                message="Analysis deleted successfully",
                data=None
            )
            
        except HTTPException:
            raise
        except Exception as e:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message=f"Failed to delete analysis: {str(e)}",
                data=None
            )
