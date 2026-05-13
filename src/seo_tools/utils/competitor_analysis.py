import asyncio
import json
from typing import Dict, List

from src.config.logger_config import setup_logger
from src.seo_tools.schemas.analyze_site_seo import CrawlMode
from src.seo_tools.schemas.competitor_analysis import CompetitorAnalysisRequest, CompetitorAnalysisResponse
from src.seo_tools.utils.competitor_analysis_report import build_competitor_analysis_payload
from src.seo_tools.utils.seo_crawler import SEOCrawler, URLStatus
from src.seo_tools.utils.seo_scraper import SEOScraper
from src.seo_tools.utils.seo_scoring import calculate_seo_score


class CompetitorAnalyzer:
    """Run two full SEO audits in parallel (same engine as analyze-site-seo)."""

    def __init__(self):
        self.logger = setup_logger(__name__)

    async def analyze(
        self, user_url: str, competitor_url: str, crawl_mode: CrawlMode, max_pages: int
    ) -> Dict:
        errors: Dict[str, str] = {}

        user_task = asyncio.create_task(self._run_site_audit(user_url, crawl_mode, max_pages))
        competitor_task = asyncio.create_task(
            self._run_site_audit(competitor_url, crawl_mode, max_pages)
        )

        user_result, competitor_result = await asyncio.gather(
            user_task, competitor_task, return_exceptions=True
        )

        if isinstance(user_result, Exception):
            errors["user"] = str(user_result)
            user_result = self._empty_site_audit(user_url, crawl_mode)
        if isinstance(competitor_result, Exception):
            errors["competitor"] = str(competitor_result)
            competitor_result = self._empty_site_audit(competitor_url, crawl_mode)

        return {
            "user_site": user_result,
            "competitor_site": competitor_result,
            "errors": errors,
        }

    async def _collect_urls(self, start_url: str, crawl_mode: CrawlMode, max_pages: int) -> List[str]:
        crawler = SEOCrawler(start_url=start_url, crawl_mode=crawl_mode)
        crawled_data = await crawler.run()

        if isinstance(crawled_data, dict):
            urls = [
                url
                for url, status in crawled_data.items()
                if status in [URLStatus.VISITED, URLStatus.SITEMAP, URLStatus.DISCOVERED]
            ]
        else:
            urls = crawled_data if isinstance(crawled_data, list) else list(crawled_data)

        if not urls:
            return [start_url]

        unique_urls = list(dict.fromkeys(urls))
        return unique_urls[: max(1, max_pages)]

    def _crawl_mode_str(self, crawl_mode: CrawlMode) -> str:
        return crawl_mode.value if hasattr(crawl_mode, "value") else str(crawl_mode)

    def _empty_site_audit(self, base_url: str, crawl_mode: CrawlMode) -> Dict:
        return {
            "target_url": base_url,
            "crawl_mode": self._crawl_mode_str(crawl_mode),
            "total_pages": 0,
            "avg_response_time_ms": None,
            "score": 0,
            "base_url_checks": {"base_url": base_url},
            "url_results": [],
        }

    async def _run_site_audit(self, base_url: str, crawl_mode: CrawlMode, max_pages: int) -> Dict:
        urls = await self._collect_urls(base_url, crawl_mode, max_pages)

        scraper = SEOScraper(base_url)
        scrape_results = await scraper.run(urls)

        base_checks_dict = json.loads(scrape_results.base_url_checks.model_dump_json())
        url_results_list = [json.loads(r.model_dump_json()) for r in scrape_results.url_results]
        score = calculate_seo_score(base_checks_dict, url_results_list)

        response_times = [
            r.get("response_time_ms") for r in url_results_list if r.get("response_time_ms")
        ]
        avg_response_time_ms = (
            sum(response_times) / len(response_times) if response_times else None
        )

        return {
            "target_url": base_url,
            "crawl_mode": self._crawl_mode_str(crawl_mode),
            "total_pages": len(url_results_list),
            "avg_response_time_ms": avg_response_time_ms,
            "score": score,
            "base_url_checks": base_checks_dict,
            "url_results": url_results_list,
        }


async def run_competitor_analysis(user_input: CompetitorAnalysisRequest) -> CompetitorAnalysisResponse:
    """Entry point for POST /seo-tools/competitor-analysis — keeps orchestration out of SeoToolsService."""
    analyzer = CompetitorAnalyzer()
    raw = await analyzer.analyze(
        user_url=str(user_input.user_url),
        competitor_url=str(user_input.competitor_url),
        crawl_mode=user_input.crawl_mode,
        max_pages=user_input.max_pages,
    )
    payload = build_competitor_analysis_payload(
        raw["user_site"],
        raw["competitor_site"],
        raw.get("errors") or {},
    )
    return CompetitorAnalysisResponse.model_validate(payload)
