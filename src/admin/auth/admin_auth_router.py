from typing import List
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_db
from src.core.security import get_current_admin, create_access_token, create_refresh_token
from src.models.user import Admin
from src.auth.schemas.user import AdminCreate, AdminLogin, AdminResponse, Token
from src.admin.auth.repository.admin_repository import AdminRepository
from src.admin.auth.admin_auth_service import AdminAuthService
from src.admin.auth.admin_auth_controller import AdminAuthController
from src.core.response_status import RESPONSE_STATUS_SUCCESS


router = APIRouter(prefix="/admin/auth", tags=["Admin - Authentication"])


def get_admin_auth_controller(db: AsyncSession = Depends(get_db)) -> AdminAuthController:
    """Dependency to get admin auth controller"""
    admin_repo = AdminRepository(db)
    service = AdminAuthService(admin_repo)
    return AdminAuthController(service)


@router.post("/register")
async def register_admin(
    admin_data: AdminCreate,
    controller: AdminAuthController = Depends(get_admin_auth_controller)
):
    """Register a new admin (Super Admin only)"""
    return await controller.register(admin_data)


@router.post("/login")
async def login_admin(
    admin_data: AdminLogin,
    response: Response,
    controller: AdminAuthController = Depends(get_admin_auth_controller)
):
    """Login as admin"""
    result = await controller.login(admin_data.email, admin_data.password)
    
    access_token = result["data"]["access_token"]
    
    response.set_cookie(
        key="admin_access_token",
        value=access_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        expires=7 * 24 * 60 * 60,
        samesite="none",
        secure=True,
        path="/",
    )

    return {
        "status": result["status"],
        "message": result["message"],
        "data": {"access_token": access_token, "token_type": "bearer"}
    }


@router.post("/logout")
async def logout_admin(response: Response):
    """Logout admin"""
    response.delete_cookie(key="admin_access_token")
    return {"status": RESPONSE_STATUS_SUCCESS, "message": "Successfully logged out", "data": None}


@router.get("/me")
async def get_admin_me(
    current_admin: Admin = Depends(get_current_admin),
    controller: AdminAuthController = Depends(get_admin_auth_controller)
):
    """Get current admin info"""
    return await controller.get_current_admin(str(current_admin.id))


@router.get("/admins")
async def get_all_admins(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    controller: AdminAuthController = Depends(get_admin_auth_controller)
):
    """Get all admins (Admin only)"""
    return await controller.get_all_admins(skip, limit)


@router.post("/refresh")
async def refresh_admin_token(
    response: Response,
    current_admin: Admin = Depends(get_current_admin)
):
    """Refresh admin access token"""
    access_token = create_access_token(
        data={"sub": str(current_admin.id), "email": current_admin.email, "role": "admin"}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(current_admin.id), "email": current_admin.email, "role": "admin"}
    )
    
    response.set_cookie(
        key="admin_access_token",
        value=access_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        expires=7 * 24 * 60 * 60,
        samesite="none",
        secure=True,
        path="/",
    )
    response.set_cookie(
        key="admin_refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=30 * 24 * 60 * 60,
        expires=30 * 24 * 60 * 60,
        samesite="none",
        secure=True,
        path="/",
    )

    return {
        "status": RESPONSE_STATUS_SUCCESS,
        "message": "Admin token refreshed successfully",
        "data": {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    }