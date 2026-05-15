from enum import Enum
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Generic, TypeVar

T = TypeVar('T')


class CrawlMode(Enum):
    SITEMAP_ONLY = "SITEMAP_ONLY"
    FULL_CRAWL = "FULL_CRAWL"


class CheckStatus(Enum):
    """Status of a check result"""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


class CheckResult(BaseModel, Generic[T]):
    """Structured result for a check with status and generic description"""
    status: CheckStatus
    description: T
    
    class Config:
        use_enum_values = True


class AnalyzeSiteSeoRequest(BaseModel):
    url: HttpUrl
    crawl_mode: CrawlMode


class BaseUrlChecks(BaseModel):
    """Checks performed only on the base URL"""
    base_url: HttpUrl
    www_redirect_check: Optional[CheckResult] = None
    robots_txt_check: Optional[CheckResult] = None
    https_ssl_check: Optional[CheckResult] = None
    directory_listing_check: Optional[CheckResult] = None
    expires_headers_check: Optional[CheckResult] = None
    caching_advice: Optional[CheckResult] = None


class AnalyzeSiteSeoResult(BaseModel):
    url: HttpUrl
    
    title: str
    title_length_check: Optional[CheckResult] = None
    title_keyword_presence: Optional[CheckResult] = None
    title_quality_guidance: Optional[str] = ""
    meta_description: Optional[str] = ""
    meta_description_length_check: Optional[CheckResult] = None
    meta_description_keyword_presence: Optional[CheckResult] = None
    meta_description_quality_guidance: Optional[str] = ""
    meta_keywords: Optional[str] = ""
    
    h1_check: Optional[CheckResult] = None
    h1_keyword_guidance: Optional[str] = ""
    h1: Optional[str] = ""
    
    h2_count: Optional[int] = 0
    h2_optimization_guidance: Optional[str] = ""
    h2: Optional[str] = ""
    
    h3: Optional[str] = ""
    
    image_alt_check: Optional[CheckResult] = None
    
    internal_links_count: Optional[int] = 0
    external_links_count: Optional[int] = 0
    links_quality_guidance: Optional[str] = ""
    
    canonical_check: Optional[CheckResult] = None
    canonical: Optional[str] = ""
    
    noindex_check: Optional[CheckResult] = None
    open_graph_check: Optional[CheckResult] = None
    schema_validation: Optional[CheckResult] = None
    
    html_size_check: Optional[CheckResult] = None
    html_size_bytes: Optional[int] = 0
    
    response_time_check: Optional[CheckResult] = None
    response_time_ms: Optional[float] = 0.0
    
    js_minification_check: Optional[CheckResult] = None
    css_minification_check: Optional[CheckResult] = None
    
    total_js_files: Optional[int] = 0
    total_css_files: Optional[int] = 0
    total_requests: Optional[int] = 0
    
    image_requests: Optional[int] = 0
    js_requests: Optional[int] = 0
    css_requests: Optional[int] = 0
    
    requests_guidance: Optional[str] = ""
    inline_css_warning: Optional[str] = ""
    
    embedded_objects_check: Optional[CheckResult] = None
    
    mobile_responsiveness: Optional[CheckResult] = None
    
    lcp: Optional[str] = ""
    fid: Optional[str] = ""
    cls: Optional[str] = ""
    
    class Config:
        populate_by_name = True


class AnalyzeSiteSeoResponse(BaseModel):
    """Response containing base URL checks and per-URL results"""
    base_url_checks: BaseUrlChecks
    url_results: List[AnalyzeSiteSeoResult]
