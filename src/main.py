from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings
import src.routers.seo_tools as seo_tools


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


@app.get("/")
async def root():
    return {"message": "Verdant Soft SEO API is running 🚀"}
