from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.config.settings import settings
from src.config.redis_client import ensure_redis_connection
from src.config.database import init_db
from src.seo_tools.seo_tools_router import router as seo_tools_router
from src.auth.auth_router import router as auth_router
from src.admin.auth.admin_auth_router import router as admin_auth_router
from src.admin.users.users_router import router as admin_users_router
from src.admin.analytics.analytics_router import router as admin_analytics_router
from src.keyword_rank.keyword_rank_router import router as keyword_rank_router
from src.keyword_suggestion.keyword_suggestion_router import router as keyword_suggestion_router
from src.seo_insight.seo_insight_router import router as seo_insight_router
from src.dashboard.dashboard_router import router as dashboard_router
from src.webhooks.routers.webhook_router import router as webhook_router, limiter as webhook_limiter
from src.webhooks.routers.management_router import router as cicd_management_router
from src.competitor_analysis.competitor_router import router as competitor_analysis_router
import logging

from src.models import *

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SEO Lens",
    description="API for site crawling, SEO analysis, and keyword research",
    version="1.0.0",
)

# Initialize rate limiter for the entire app
app.state.limiter = webhook_limiter

# Add rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please slow down your requests.",
            "retry_after": "60 seconds"
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://seo-lens-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# Include routers
app.include_router(auth_router)
app.include_router(admin_auth_router)
app.include_router(admin_users_router)
app.include_router(admin_analytics_router)
app.include_router(seo_tools_router)
app.include_router(keyword_rank_router)
app.include_router(keyword_suggestion_router)
app.include_router(seo_insight_router)
app.include_router(dashboard_router)
app.include_router(webhook_router)
app.include_router(cicd_management_router)
app.include_router(competitor_analysis_router)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info("Starting up...")
    await ensure_redis_connection()
    logger.info("Application ready!")
    logger.info("To create database tables, run: make init-db")


@app.get("/")
async def root():
    return {"message": "Verdant Soft SEO API is running 🚀", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/seo-test-ui")
async def seo_test_ui():
    """Serve the SEO Test UI"""
    ui_path = Path(__file__).parent / "static" / "seo_test_ui.html"
    if ui_path.exists():
        return FileResponse(ui_path)
    return {"error": "UI file not found"}