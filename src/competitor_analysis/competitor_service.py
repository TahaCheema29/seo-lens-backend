"""
Competitor Analysis Service
Main service for orchestrating competitor analysis with 3 modes
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from src.models.competitor_analysis import (
    CompetitorAnalysis, 
    CompetitorAnalysisMode, 
    CompetitorAnalysisStatus
)
from src.competitor_analysis.competitor_repository import CompetitorAnalysisRepository
from src.competitor_analysis.analyzers import QuickAnalyzer, FullAnalyzer
from src.competitor_analysis.engines import (
    ComparisonEngine, 
    SuggestionEngine, 
    QuickWinDetector
)
from src.seo_tools.utils.seo_crawler import CrawlMode
from src.config.logger_config import setup_logger


class CompetitorAnalysisService:
    """
    Service for competitor analysis
    Supports 3 modes: QUICK, SITEMAP_ONLY, FULL_CRAWL
    """
    
    def __init__(self, repository: CompetitorAnalysisRepository):
        self.repository = repository
        self.logger = setup_logger(__name__)
        
        # Initialize analyzers and engines
        self.quick_analyzer = QuickAnalyzer()
        self.full_analyzer = FullAnalyzer()
        self.comparison_engine = ComparisonEngine()
        self.suggestion_engine = SuggestionEngine()
        self.quick_win_detector = QuickWinDetector()
    
    async def analyze_competitors(
        self,
        user_url: str,
        competitor_url: str,
        mode: CompetitorAnalysisMode,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for competitor analysis
        
        Args:
            user_url: User's website URL
            competitor_url: Competitor's website URL
            mode: Analysis mode (QUICK, SITEMAP_ONLY, FULL_CRAWL)
            user_id: Optional user ID for authenticated users
            
        Returns:
            Complete analysis response
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Step 1: Create analysis record
            analysis = CompetitorAnalysis(
                user_id=user_id,
                user_url=user_url,
                competitor_url=competitor_url,
                crawl_mode=mode,
                status=CompetitorAnalysisStatus.PROCESSING
            )
            await self.repository.create(analysis)
            
            self.logger.info(f"Started {mode.value} analysis: {user_url} vs {competitor_url}")
            
            # Step 2: Run both analyses in PARALLEL
            user_task = self._analyze_site(user_url, mode)
            competitor_task = self._analyze_site(competitor_url, mode)
            
            user_result, competitor_result = await asyncio.gather(
                user_task,
                competitor_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(user_result, Exception):
                self.logger.error(f"Error analyzing user site: {user_result}")
                await self.repository.update_status(
                    str(analysis.id),
                    CompetitorAnalysisStatus.FAILED,
                    f"Failed to analyze user site: {str(user_result)}"
                )
                raise user_result
            
            if isinstance(competitor_result, Exception):
                self.logger.error(f"Error analyzing competitor site: {competitor_result}")
                await self.repository.update_status(
                    str(analysis.id),
                    CompetitorAnalysisStatus.FAILED,
                    f"Failed to analyze competitor site: {str(competitor_result)}"
                )
                raise competitor_result
            
            self.logger.info("Both analyses completed successfully")
            
            # Step 3: Calculate scores
            user_score = self.comparison_engine.calculate_overall_score(user_result)
            competitor_score = self.comparison_engine.calculate_overall_score(competitor_result)
            
            # Step 4: Generate comparison
            comparison = self.comparison_engine.compare_metrics(user_result, competitor_result)
            
            # Step 5: Generate suggestions
            suggestions = self.suggestion_engine.generate_suggestions(
                comparison, user_score, competitor_score
            )
            
            # Step 6: Generate quick wins
            quick_wins = self.quick_win_detector.detect_quick_wins(user_result, comparison)
            
            # Step 7: Generate strengths and weaknesses
            strengths = self.suggestion_engine.generate_strengths(comparison)
            weaknesses = self.suggestion_engine.generate_weaknesses(comparison)
            
            # Step 8: Determine winner
            winner = self.comparison_engine.determine_winner(user_score, competitor_score)
            score_gap = abs(user_score - competitor_score)
            
            # Step 9: Generate summary
            summary = self.comparison_engine.generate_summary(user_score, competitor_score, comparison)
            
            # Step 10: Serialize data for database storage
            # Convert Pydantic models and HttpUrl objects to JSON-serializable dicts
            user_seo_data_json = self._serialize_seo_data(user_result)
            competitor_seo_data_json = self._serialize_seo_data(competitor_result)
            
            # Step 11: Update database with results
            await self.repository.update_results(
                analysis_id=str(analysis.id),
                user_seo_data=user_seo_data_json,
                competitor_seo_data=competitor_seo_data_json,
                user_score=user_score,
                competitor_score=competitor_score,
                winner=winner,
                score_gap=score_gap,
                comparison_report=comparison,
                suggestions=suggestions,
                quick_wins=quick_wins,
                strengths=strengths,
                weaknesses=weaknesses
            )
            
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(f"Analysis completed in {duration:.1f} seconds")
            
            # Step 11: Build response
            return self._build_response(
                analysis=analysis,
                user_url=user_url,
                competitor_url=competitor_url,
                mode=mode,
                user_score=user_score,
                competitor_score=competitor_score,
                winner=winner,
                score_gap=score_gap,
                summary=summary,
                comparison=comparison,
                suggestions=suggestions,
                quick_wins=quick_wins,
                strengths=strengths,
                weaknesses=weaknesses,
                user_result=user_result,
                competitor_result=competitor_result,
                start_time=start_time,
                end_time=end_time,
                duration=duration
            )
            
        except Exception as e:
            self.logger.error(f"Error in analyze_competitors: {e}")
            raise
    
    async def _analyze_site(self, url: str, mode: CompetitorAnalysisMode) -> Dict[str, Any]:
        """
        Analyze a single site based on mode
        
        Args:
            url: Site URL
            mode: Analysis mode
            
        Returns:
            SEO analysis data
        """
        if mode == CompetitorAnalysisMode.QUICK:
            # Quick mode: homepage only
            return await self.quick_analyzer.analyze_homepage(url)
        elif mode == CompetitorAnalysisMode.SITEMAP_ONLY:
            # Sitemap mode: up to 100 pages from sitemap
            return await self.full_analyzer.analyze_site(url, CrawlMode.SITEMAP_ONLY)
        else:
            # Full crawl mode: up to 100 pages discovered
            return await self.full_analyzer.analyze_site(url, CrawlMode.FULL_CRAWL)
    
    def _serialize_seo_data(self, seo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize SEO data to JSON-compatible format
        Handles Pydantic models, HttpUrl objects, and other non-serializable types
        """
        from pydantic import HttpUrl, BaseModel
        
        def convert_value(value):
            if isinstance(value, HttpUrl):
                return str(value)
            elif isinstance(value, BaseModel):
                return convert_value(value.model_dump())
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [convert_value(item) for item in value]
            elif isinstance(value, set):
                return [convert_value(item) for item in value]
            elif hasattr(value, 'value'):  # Enum
                return value.value
            else:
                return value
        
        return convert_value(seo_data)
    
    def _build_response(
        self,
        analysis: CompetitorAnalysis,
        user_url: str,
        competitor_url: str,
        mode: CompetitorAnalysisMode,
        user_score: int,
        competitor_score: int,
        winner: str,
        score_gap: int,
        summary: Dict[str, Any],
        comparison: Dict[str, Any],
        suggestions: list,
        quick_wins: list,
        strengths: list,
        weaknesses: list,
        user_result: Dict[str, Any],
        competitor_result: Dict[str, Any],
        start_time: datetime,
        end_time: datetime,
        duration: float
    ) -> Dict[str, Any]:
        """Build the complete response with comprehensive analysis"""
        
        # Generate page-by-page breakdown
        page_breakdown = self.comparison_engine.generate_page_breakdown(
            user_result, competitor_result
        )
        
        # Generate action priority matrix
        action_matrix = self.comparison_engine.generate_action_priority_matrix(
            comparison, user_score, competitor_score
        )
        
        # Get URLs crawled
        user_urls = [r.get("url", "") for r in user_result.get("url_results", [])]
        comp_urls = [r.get("url", "") for r in competitor_result.get("url_results", [])]
        
        return {
            "analysis_id": str(analysis.id),
            "mode": mode.value,
            "status": "completed",
            
            "urls": {
                "user": user_url,
                "competitor": competitor_url
            },
            
            "analysis_meta": {
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_seconds": round(duration, 1),
                "pages_analyzed": {
                    "user": len(user_result.get("url_results", [])),
                    "competitor": len(competitor_result.get("url_results", []))
                },
                "urls_crawled": {
                    "user": user_urls[:10],  # First 10 URLs
                    "competitor": comp_urls[:10]
                }
            },
            
            "overall_scores": {
                "user": user_score,
                "competitor": competitor_score,
                "winner": winner,
                "gap": score_gap,
                "interpretation": summary.get("headline", "")
            },
            
            "comparison_summary": summary,
            
            "detailed_comparison": comparison,
            
            "comparison_matrix": {
                "where_you_win": strengths,
                "where_you_lose": weaknesses,
                "tie": self._generate_tie_items(comparison)
            },
            
            "suggestions": suggestions,
            
            "quick_wins": quick_wins,
            
            "strengths_to_maintain": strengths,
            
            "page_breakdown": page_breakdown,
            
            "action_priority_matrix": action_matrix,
            
            "created_at": analysis.created_at.isoformat()
        }
    
    def _generate_tie_items(self, comparison: Dict[str, Any]) -> list:
        """Generate tie items where both are equal"""
        ties = []
        
        perf = comparison.get("performance", {})
        seo = comparison.get("seo", {})
        tech = comparison.get("technical", {})
        
        # Check for ties
        if perf.get("load_time", {}).get("winner") == "tie":
            ties.append({
                "category": "performance",
                "metric": "Load Time",
                "status": "Both equal",
                "note": "Both sites have similar loading speeds"
            })
        
        if tech.get("https_security", {}).get("winner") == "tie":
            ties.append({
                "category": "technical",
                "metric": "HTTPS Security",
                "status": "Both secure",
                "note": "Both sites have proper SSL certificates"
            })
        
        return ties
    
    async def get_analysis_by_id(self, analysis_id: str) -> Optional[CompetitorAnalysis]:
        """Get analysis by ID"""
        return await self.repository.get_by_id(analysis_id)
    
    async def get_user_analyses(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get analyses for a user"""
        try:
            items = await self.repository.get_by_user(user_id, skip, limit)
            total = await self.repository.count_by_user(user_id)
            
            return {
                "success": True,
                "data": {
                    "items": [
                        {
                            "analysis_id": str(item.id),
                            "user_url": item.user_url,
                            "competitor_url": item.competitor_url,
                            "mode": item.crawl_mode.value,
                            "status": item.status.value,
                            "user_score": item.user_score,
                            "competitor_score": item.competitor_score,
                            "winner": item.winner.value if item.winner else None,
                            "created_at": item.created_at.isoformat()
                        }
                        for item in items
                    ],
                    "total": total
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting user analyses: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_analysis(self, user_id: str, analysis_id: str) -> bool:
        """Delete an analysis"""
        try:
            # Verify ownership
            analysis = await self.repository.get_by_user_and_id(user_id, analysis_id)
            if not analysis:
                return False
            
            return await self.repository.delete(analysis_id)
        except Exception as e:
            self.logger.error(f"Error deleting analysis: {e}")
            return False
