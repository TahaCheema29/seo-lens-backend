import enum
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Enum, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from src.config.database import Base
from src.models.base import BaseModel


class CompetitorAnalysisStatus(str, enum.Enum):
    """Status of competitor analysis"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CompetitorAnalysisMode(str, enum.Enum):
    """Crawl mode for competitor analysis"""
    QUICK = "QUICK"
    SITEMAP_ONLY = "SITEMAP_ONLY"
    FULL_CRAWL = "FULL_CRAWL"


class CompetitorAnalysisWinner(str, enum.Enum):
    """Winner of the comparison"""
    USER = "user"
    COMPETITOR = "competitor"
    TIE = "tie"


class CompetitorAnalysis(Base, BaseModel):
    """Store competitor analysis results"""
    __tablename__ = "competitor_analyses"
    
    # User association (optional for anonymous users)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # URLs analyzed
    user_url = Column(String, nullable=False, index=True)
    competitor_url = Column(String, nullable=False, index=True)
    
    # Crawl configuration
    crawl_mode = Column(Enum(CompetitorAnalysisMode), nullable=False, default=CompetitorAnalysisMode.QUICK)
    
    # SEO data storage (JSON for flexibility)
    user_seo_data = Column(JSON, nullable=True, default=dict)
    competitor_seo_data = Column(JSON, nullable=True, default=dict)
    
    # Scores
    user_score = Column(Integer, nullable=True)
    competitor_score = Column(Integer, nullable=True)
    winner = Column(Enum(CompetitorAnalysisWinner), nullable=True)
    score_gap = Column(Integer, nullable=True)
    
    # Analysis results
    comparison_report = Column(JSON, nullable=True, default=dict)
    suggestions = Column(JSON, nullable=True, default=list)
    quick_wins = Column(JSON, nullable=True, default=list)
    strengths = Column(JSON, nullable=True, default=list)
    weaknesses = Column(JSON, nullable=True, default=list)
    
    # Status tracking
    status = Column(Enum(CompetitorAnalysisStatus), nullable=False, default=CompetitorAnalysisStatus.PENDING)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="competitor_analyses", lazy="selectin")
    
    def __repr__(self):
        return f"<CompetitorAnalysis {self.user_url} vs {self.competitor_url}>"
