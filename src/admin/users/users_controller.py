from fastapi import HTTPException, status
from src.admin.users.users_service import UsersService
from src.auth.repository.user_repository import UserRepository
from src.auth.schemas.user import UserResponse
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS, RESPONSE_STATUS_ERROR


class UsersController:
    """Controller for user management operations"""
    
    def __init__(self, service: UsersService):
        self.service = service
    
    async def get_all_users(self, skip: int, limit: int) -> dict:
        """Get all users"""
        return await self.service.get_all_users(skip, limit)
    
    async def get_user_by_id(self, user_id: str) -> dict:
        """Get user by ID"""
        result = await self.service.get_user_by_id(user_id)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        
        return result
    
    async def activate_user(self, user_id: str) -> dict:
        """Activate user"""
        result = await self.service.activate_user(user_id)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        
        return result
    
    async def deactivate_user(self, user_id: str) -> dict:
        """Deactivate user"""
        result = await self.service.deactivate_user(user_id)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        
        return result
    
    async def update_user_role(self, user_id: str, role: str) -> dict:
        """Update user role"""
        result = await self.service.update_user_role(user_id, role)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
    
    async def delete_user(self, user_id: str) -> dict:
        """Delete user"""
        result = await self.service.delete_user(user_id)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        
        return result