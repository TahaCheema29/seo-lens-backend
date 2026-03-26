import json
import redis.asyncio as redis
from fastapi import APIRouter, Depends, status, WebSocket, WebSocketDisconnect, Query
from urllib.parse import urlparse

from src.config.settings import settings
from src.seo_tools.seo_tools_controller import SeoToolsController
from src.seo_tools.schemas.analyze_keyword_rank import AnalyzeKeywordRankRequest
from src.seo_tools.schemas.suggest_keywords import SuggestKeywordRequest
from src.seo_tools.schemas.analyze_site_seo import AnalyzeSiteSeoRequest


router = APIRouter(prefix="/seo-tools", tags=["SEO Tools"])


def get_seo_tools_controller() -> SeoToolsController:
    return SeoToolsController()


@router.post("/analyze-rank", status_code=status.HTTP_200_OK)
async def analyze_keyword_rank(
    user_input: AnalyzeKeywordRankRequest,
    seo_tools_controller: SeoToolsController = Depends(get_seo_tools_controller),
):
    return await seo_tools_controller.analyze_keyword_rank(user_input)


@router.post("/suggest-keywords", status_code=status.HTTP_200_OK)
async def suggest_keywords(
    user_input: SuggestKeywordRequest,
    seo_tools_controller: SeoToolsController = Depends(get_seo_tools_controller),
):
    return await seo_tools_controller.suggest_keywords(user_input)


@router.post("/analyze-site-seo", status_code=status.HTTP_200_OK)
async def analyze_site_seo(
    user_input: AnalyzeSiteSeoRequest,
    seo_tools_controller: SeoToolsController = Depends(get_seo_tools_controller),
    crawl_id: str = Query(None, description="Crawl ID for live preview"),
):
    import logging
    logger = logging.getLogger(__name__)

    print("analyze_site_seo called with crawl_id:", crawl_id)
    try:
        logger.info(f"Received analyze-site-seo request for {user_input.url}, crawl_id: {crawl_id}")
        result = await seo_tools_controller.analyze_site_seo(user_input, crawl_id=crawl_id)
        logger.info("analyze-site-seo request completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in analyze-site-seo endpoint: {e}", exc_info=True)
        raise


@router.websocket("/ws/crawl/{crawl_id}")
async def websocket_crawl_preview(websocket: WebSocket, crawl_id: str):
    """WebSocket endpoint for live crawl preview streaming via Redis pub/sub"""
    await websocket.accept()

    parsed = urlparse(settings.redis_url)
    
    ws_redis_client = redis.Redis(
        host=parsed.hostname or 'redis',
        port=parsed.port or 6379,
        password=parsed.password or None,
        db=int(parsed.path.lstrip('/')) if parsed.path and parsed.path != '/' else 0,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )
    
    print("WebSocket Redis client created ", ws_redis_client)
    pubsub = None
    try:
        pubsub = ws_redis_client.pubsub()
        await pubsub.subscribe(f"crawl:{crawl_id}")

        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket Redis error: {e}")
    finally:
        try:
            if pubsub:
                await pubsub.unsubscribe(f"crawl:{crawl_id}")
                await pubsub.aclose()
            await ws_redis_client.aclose()
        except:
            pass