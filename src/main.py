from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from src.config.settings import settings
from src.config.redis_client import ensure_redis_connection
from src.config.schema_ensure import ensure_status_columns
from src.config.database import init_db
from src.seo_tools.seo_tools_router import router as seo_tools_router
from src.auth.auth_router import router as auth_router
from src.admin.auth.admin_auth_router import router as admin_auth_router
from src.admin.users.users_router import router as admin_users_router
from src.keyword_rank.keyword_rank_router import router as keyword_rank_router
from src.keyword_suggestion.keyword_suggestion_router import router as keyword_suggestion_router
from src.seo_insight.seo_insight_router import router as seo_insight_router
from src.dashboard.dashboard_router import router as dashboard_router
import logging

from src.models import *

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SEO Lens",
    description="API for site crawling, SEO analysis, and keyword research",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(admin_auth_router)
app.include_router(admin_users_router)
app.include_router(seo_tools_router)
app.include_router(keyword_rank_router)
app.include_router(keyword_suggestion_router)
app.include_router(seo_insight_router)
app.include_router(dashboard_router)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info("Starting up...")
    await ensure_redis_connection()
    await ensure_status_columns()
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