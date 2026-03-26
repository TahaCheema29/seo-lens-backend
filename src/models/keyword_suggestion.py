from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from src.config.database import Base
from .base import BaseModel


class KeywordSuggestion(Base, BaseModel):
    """Store keyword suggestion/research results"""
    __tablename__ = "keyword_suggestions"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    primary_keyword = Column(String, nullable=False, index=True)
    
    search_results = Column(JSON, nullable=False, default=list)
    related_searches = Column(JSON, nullable=False, default=list)
    people_also_ask = Column(JSON, nullable=False, default=list)
    autocomplete_suggestions = Column(JSON, nullable=False, default=list)
    long_tail_keywords = Column(JSON, nullable=False, default=list)
    
    total_related_terms = Column(Integer, nullable=False, default=0)
    timestamp = Column(Float, nullable=False)
    date = Column(Text, nullable=False)
    
    user = relationship("User", back_populates="keyword_suggestions")
    
    def __repr__(self):
        return f"<KeywordSuggestion {self.primary_keyword}>"