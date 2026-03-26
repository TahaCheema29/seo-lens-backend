from typing import List
from fastapi import HTTPException, status
from src.auth.repository.user_repository import UserRepository
from src.models.user import User, UserRole
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS, RESPONSE_STATUS_ERROR


class UsersService:
    """Service for user management operations"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> dict:
        """Get all users with pagination"""
        users = await self.user_repo.get_all(skip, limit)
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Users retrieved successfully",
            data=users
        )
    
    async def get_user_by_id(self, user_id: str) -> dict:
        """Get user by ID"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="User not found",
                data=None
            )
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="User retrieved successfully",
            data=user
        )
    
    async def activate_user(self, user_id: str) -> dict:
        """Activate user"""
        user = await self.user_repo.activate(user_id)
        if not user:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="User not found",
                data=None
            )
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="User activated successfully",
            data=user
        )
    
    async def deactivate_user(self, user_id: str) -> dict:
        """Deactivate user"""
        user = await self.user_repo.deactivate(user_id)
        if not user:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="User not found",
                data=None
            )
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="User deactivated successfully",
            data=user
        )
    
    async def update_user_role(self, user_id: str, role: str) -> dict:
        """Update user role"""
        try:
            user_role = UserRole(role.lower())
        except ValueError:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message=f"Invalid role. Must be one of: {[r.value for r in UserRole]}",
                data=None
            )
        
        user = await self.user_repo.update_role(user_id, user_role)
        if not user:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="User not found",
                data=None
            )
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="User role updated successfully",
            data=user
        )
    
    async def delete_user(self, user_id: str) -> dict:
        """Delete user"""
        deleted = await self.user_repo.delete(user_id)
        if not deleted:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="User not found",
                data=None
            )
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="User deleted successfully",
            data=None
        )