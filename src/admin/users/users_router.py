from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_db
from src.core.security import get_current_admin_user
from src.models.user import User
from src.auth.repository.user_repository import UserRepository
from src.admin.users.users_service import UsersService
from src.admin.users.users_controller import UsersController
from src.auth.schemas.user import UserResponse


router = APIRouter(prefix="/admin/users", tags=["Admin - User Management"])


def get_users_controller(db: AsyncSession = Depends(get_db)) -> UsersController:
    """Dependency to get users controller"""
    user_repo = UserRepository(db)
    service = UsersService(user_repo)
    return UsersController(service)


@router.get("")
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_current_admin_user),
    controller: UsersController = Depends(get_users_controller)
):
    """Get all users (Admin only)"""
    return await controller.get_all_users(skip, limit)


@router.get("/{user_id}")
async def get_user_by_id(
    user_id: str,
    admin_user: User = Depends(get_current_admin_user),
    controller: UsersController = Depends(get_users_controller)
):
    """Get a specific user by ID (Admin only)"""
    return await controller.get_user_by_id(user_id)


@router.put("/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin_user: User = Depends(get_current_admin_user),
    controller: UsersController = Depends(get_users_controller)
):
    """Activate a user account (Admin only)"""
    return await controller.activate_user(user_id)


@router.put("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin_user: User = Depends(get_current_admin_user),
    controller: UsersController = Depends(get_users_controller)
):
    """Deactivate a user account (Admin only)"""
    return await controller.deactivate_user(user_id)


@router.put("/{user_id}/role/{role}")
async def update_user_role(
    user_id: str,
    role: str,
    admin_user: User = Depends(get_current_admin_user),
    controller: UsersController = Depends(get_users_controller)
):
    """Update user role (Admin only)"""
    return await controller.update_user_role(user_id, role)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    admin_user: User = Depends(get_current_admin_user),
    controller: UsersController = Depends(get_users_controller)
):
    """Delete a user (Admin only)"""
    return await controller.delete_user(user_id)