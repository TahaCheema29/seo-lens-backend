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
    
    # Basic SEO - Title & Description
    title: str
    title_length_check: Optional[str] = ""
    title_keyword_presence: Optional[str] = ""
    title_quality_guidance: Optional[str] = ""
    meta_description: Optional[str] = ""
    meta_description_length_check: Optional[str] = ""
    meta_description_keyword_presence: Optional[str] = ""
    meta_description_quality_guidance: Optional[str] = ""
    meta_keywords: Optional[str] = ""
    
    # Basic SEO - Headings
    h1_check: Optional[str] = ""
    h1_keyword_guidance: Optional[str] = ""
    h1: Optional[str] = ""
    h2_count: Optional[int] = 0
    h2_optimization_guidance: Optional[str] = ""
    h2: Optional[str] = ""
    h3: Optional[str] = ""
    
    # Basic SEO - Images
    image_alt_check: Optional[str] = ""
    
    # Basic SEO - Links
    internal_links_count: Optional[int] = 0
    external_links_count: Optional[int] = 0
    links_quality_guidance: Optional[str] = ""
    
    # Advanced SEO
    canonical_check: Optional[str] = ""
    canonical: Optional[str] = ""
    noindex_check: Optional[str] = ""
    www_redirect_check: Optional[str] = ""
    robots_txt_check: Optional[str] = ""
    open_graph_check: Optional[str] = ""
    schema_validation: Optional[str] = ""
    
    # Performance
    html_size_check: Optional[str] = ""
    html_size_bytes: Optional[int] = 0
    response_time_check: Optional[str] = ""
    response_time_ms: Optional[float] = 0.0
    expires_headers_check: Optional[str] = ""
    caching_advice: Optional[str] = ""
    js_minification_check: Optional[str] = ""
    css_minification_check: Optional[str] = ""
    total_js_files: Optional[int] = 0
    total_css_files: Optional[int] = 0
    total_requests: Optional[int] = 0
    image_requests: Optional[int] = 0
    js_requests: Optional[int] = 0
    css_requests: Optional[int] = 0
    requests_guidance: Optional[str] = ""
    inline_css_warning: Optional[str] = ""
    embedded_objects_check: Optional[str] = ""
    
    # Security
    https_ssl_check: Optional[str] = ""
    directory_listing_check: Optional[str] = ""
    safe_browsing_check: Optional[str] = ""
    
    # Mobile
    mobile_responsiveness: Optional[str] = ""
    
    # Core Web Vitals
    lcp: Optional[str] = "-"
    fid: Optional[str] = "-"
    cls: Optional[str] = "-"

    class Config:
        populate_by_name = True
