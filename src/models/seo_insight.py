from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from src.config.database import Base
from .base import BaseModel


class SeoInsightResult(Base, BaseModel):
    """Store SEO site analysis results"""
    __tablename__ = "seo_insight_results"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_url = Column(String, nullable=False, index=True)
    crawl_mode = Column(String, nullable=False)
    
    base_url_checks = Column(JSON, nullable=False)
    url_results = Column(JSON, nullable=False, default=list)
    
    total_pages = Column(Integer, nullable=False, default=0)
    avg_response_time_ms = Column(Float, nullable=True)
    
    user = relationship("User", back_populates="seo_insights")
    
    def __repr__(self):
        return f"<SeoInsightResult {self.target_url}>"