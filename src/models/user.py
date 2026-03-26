import enum
from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship
from src.config.database import Base
from .base import BaseModel


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base, BaseModel):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    keyword_ranks = relationship("KeywordRankResult", back_populates="user", cascade="all, delete-orphan")
    keyword_suggestions = relationship("KeywordSuggestion", back_populates="user", cascade="all, delete-orphan")
    seo_insights = relationship("SeoInsightResult", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"

class Admin(Base, BaseModel):
    __tablename__ = "admins"
    
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_super_admin = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<Admin {self.email}>"