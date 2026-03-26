from fastapi import HTTPException, status
from src.admin.auth.repository.admin_repository import AdminRepository
from src.admin.auth.admin_auth_service import AdminAuthService
from src.auth.schemas.user import AdminResponse
from src.core.security import create_access_token
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS, RESPONSE_STATUS_ERROR


class AdminAuthController:
    """Controller for admin authentication operations"""
    
    def __init__(self, service: AdminAuthService):
        self.service = service
    
    async def register(self, admin_data) -> dict:
        """Register a new admin"""
        result = await self.service.register(admin_data)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
    
    async def login(self, email: str, password: str) -> dict:
        """Login admin"""
        result = await self.service.authenticate(email, password)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["message"]
            )
        
        admin = result["data"]
        access_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})
        
        return {
            "status": RESPONSE_STATUS_SUCCESS,
            "message": "Login successful",
            "data": {
                "admin": AdminResponse.model_validate(admin),
                "access_token": access_token
            }
        }
    
    async def get_current_admin(self, admin_id: str) -> dict:
        """Get current admin"""
        result = await self.service.get_admin_by_id(admin_id)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["message"]
            )
        
        return result
    
    async def get_all_admins(self, skip: int, limit: int) -> dict:
        """Get all admins"""
        return await self.service.get_all_admins(skip, limit)
    
    async def update_admin(self, admin_id: str, admin_data) -> dict:
        """Update admin"""
        return await self.service.update_admin(admin_id, admin_data)
    
    async def delete_admin(self, admin_id: str) -> dict:
        """Delete admin"""
        return await self.service.delete_admin(admin_id)