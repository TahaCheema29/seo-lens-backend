from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from src.config.database import Base
from .base import BaseModel


class KeywordRankResult(Base, BaseModel):
    """Store keyword rank analysis results"""
    __tablename__ = "keyword_rank_results"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_url = Column(String, nullable=False, index=True)
    keywords = Column(JSON, nullable=False)
    
    keyword = Column(String, nullable=False, index=True)
    target_domain = Column(String, nullable=True)
    target_position = Column(Integer, nullable=True)
    total_results = Column(Integer, nullable=False)
    search_results = Column(JSON, nullable=False)
    
    timestamp = Column(Float, nullable=False)
    date = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="completed")
    
    user = relationship("User", back_populates="keyword_ranks")
    
    def __repr__(self):
        return f"<KeywordRankResult {self.keyword} - {self.target_domain}>"