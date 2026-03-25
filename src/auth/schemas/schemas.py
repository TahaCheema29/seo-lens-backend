from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    # bcrypt has a 72-byte limit; enforcing this avoids runtime hashing errors.
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CreateReportRequest(BaseModel):
    report_type: str = Field(min_length=1, max_length=100)
    report: Dict[str, Any]


class UpdateReportRequest(BaseModel):
    report: Dict[str, Any]
    report_type: Optional[str] = Field(default=None, min_length=1, max_length=100)

