from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: UUID
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Message(BaseModel):
    message: str


# Admin Schemas
class AdminBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class AdminCreate(AdminBase):
    password: str = Field(..., min_length=8)


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class AdminResponse(AdminBase):
    id: UUID
    is_active: bool
    is_super_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdminUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)