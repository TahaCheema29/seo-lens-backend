from fastapi import APIRouter, Depends, status

from src.controllers.seo_tools import SeoToolsController
from src.schemas.analyze_keyword_rank import AnalyzeKeywordRankRequest
from src.schemas.suggest_keywords import SuggestKeywordRequest
from src.schemas.analyze_site_seo import AnalyzeSiteSeoRequest


router = APIRouter(prefix="/seo-tools", tags=["SEO Tools"])


def get_seo_tools_controller() -> SeoToolsController:
    return SeoToolsController()


@router.post("/analyze-rank", status_code=status.HTTP_200_OK)
async def analyze_keyword_rank(
    user_input: AnalyzeKeywordRankRequest,
    seo_tools_controller: SeoToolsController = Depends(get_seo_tools_controller),
):
    return await seo_tools_controller.analyze_keyword_rank(user_input)
    # return {}


@router.post("/suggest-keywords",status_code=status.HTTP_200_OK)
async def suggest_keywords(
    user_input:SuggestKeywordRequest,
    seo_tools_controller:SeoToolsController=Depends(get_seo_tools_controller)
):
    return await seo_tools_controller.suggest_keywords(user_input)


@router.post("/analyze-site-seo",status_code=status.HTTP_200_OK)
async def analyze_site_seo(
    user_input:AnalyzeSiteSeoRequest,
    seo_tools_controller:SeoToolsController=Depends(get_seo_tools_controller)
):
    return await seo_tools_controller.analyze_site_seo(user_input)
