from enum import Enum
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional


class CrawlMode(Enum):
    SITEMAP_ONLY = "SITEMAP_ONLY"
    FULL_CRAWL = "FULL_CRAWL"


class AnalyzeSiteSeoRequest(BaseModel):
    url: HttpUrl
    crawl_mode: CrawlMode


class AnalyzeSiteSeoResult(BaseModel):
    url: HttpUrl
    title: str
    meta_description: Optional[str] = ""
    meta_keywords: Optional[str] = ""
    h1: Optional[str] = ""
    h2: Optional[str] = ""
    h3: Optional[str] = ""
    alt_check: Optional[str] = ""
    canonical: Optional[str] = ""
    mobile_responsiveness: Optional[str] = ""
    schema_validation: Optional[str] = ""
    lcp: Optional[str] = "-"
    fid: Optional[str] = "-"
    cls: Optional[str] = "-"

    class Config:
        populate_by_name = True
