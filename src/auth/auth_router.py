from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.auth.schemas.user import UserCreate, UserLogin, UserResponse, UserUpdate, Token
from src.auth.repository.user_repository import UserRepository
from src.auth.auth_controller import AuthController
from src.core.security import create_access_token, create_refresh_token, decode_access_token
from src.core.response_status import RESPONSE_STATUS_SUCCESS
from typing import Any, Dict


router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_controller(db: AsyncSession = Depends(get_db)) -> AuthController:
    """Dependency to get auth controller"""
    user_repo = UserRepository(db)
    subscription_repo = SubscriptionRepository(db)
    return AuthController(user_repo, subscription_repo)


@router.post("/register")
async def register(
    user_data: UserCreate,
    controller: AuthController = Depends(get_auth_controller)
):
    """Register a new user"""
    return await controller.register(user_data)


@router.post("/login")
async def login(
    user_data: UserLogin,
    response: Response,
    controller: AuthController = Depends(get_auth_controller)
):
    """Login and set HTTP-only cookie with JWT token"""
    result = await controller.login(user_data.email, user_data.password)
    
    access_token = result["data"]["access_token"]
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        expires=7 * 24 * 60 * 60,
        samesite="lax",
        secure=False,
    )
    
    return {
        "status": result["status"],
        "message": result["message"],
        "data": {"access_token": access_token, "token_type": "bearer"}
    }


@router.post("/logout")
async def logout(response: Response):
    """Logout and clear the HTTP-only cookie"""
    response.delete_cookie(key="access_token")
    return {"status": RESPONSE_STATUS_SUCCESS, "message": "Successfully logged out", "data": None}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return {
        "status": RESPONSE_STATUS_SUCCESS,
        "message": "User retrieved successfully",
        "data": UserResponse.model_validate(current_user)
    }


@router.put("/me")
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller)
):
    """Update current user information"""
    return await controller.update_user(str(current_user.id), user_data)


@router.delete("/me")
async def delete_me(
    current_user: User = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller)
):
    """Delete current user account"""
    return await controller.delete_user(str(current_user.id))


@router.post("/refresh")
async def refresh_token(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Refresh access token using valid JWT token"""
    access_token = create_access_token(
        data={"sub": str(current_user.id), "email": current_user.email}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(current_user.id), "email": current_user.email}
    )
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        expires=7 * 24 * 60 * 60,
        samesite="lax",
        secure=False,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=30 * 24 * 60 * 60,
        expires=30 * 24 * 60 * 60,
        samesite="lax",
        secure=False,
    )
    
    return {
        "status": RESPONSE_STATUS_SUCCESS,
        "message": "Token refreshed successfully",
        "data": {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    }