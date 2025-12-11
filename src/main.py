from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from src.config.settings import settings
from src.config.redis_client import ensure_redis_connection
import src.routers.seo_tools as seo_tools
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SEO Lens",
    description="API for site crawling and SEO analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(seo_tools.router)


@app.on_event("startup")
async def startup_event():
    """Verify Redis connection on startup"""
    logger.info("Starting up...")
    await ensure_redis_connection()


@app.get("/")
async def root():
    return {"message": "Verdant Soft SEO API is running 🚀"}


@app.get("/seo-test-ui")
async def seo_test_ui():
    """Serve the SEO Test UI"""
    ui_path = Path(__file__).parent / "static" / "seo_test_ui.html"
    if ui_path.exists():
        return FileResponse(ui_path)
    return {"error": "UI file not found"}
