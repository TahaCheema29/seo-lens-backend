from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings
import src.routers.seo_tools as seo_tools
from src.auth.schemas.db import init_auth_db
import src.auth.routers.auth_router as auth_router


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
app.include_router(auth_router.router)


@app.on_event("startup")
async def on_startup() -> None:
    # Creates the auth tables if they don't exist yet.
    await init_auth_db()


@app.get("/")
async def root():
    return {"message": "Verdant Soft SEO API is running 🚀"}
