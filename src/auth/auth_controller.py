from fastapi import HTTPException, status
from src.auth.repository.user_repository import UserRepository
from src.auth.auth_service import AuthService
from src.billing.subscription_repository import SubscriptionRepository
from src.models.user import User
from src.auth.schemas.user import UserCreate, UserUpdate
from src.core.security import create_access_token
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS, RESPONSE_STATUS_ERROR


class AuthController:
    """Controller for authentication operations"""
    
    def __init__(self, user_repo: UserRepository, subscription_repo: SubscriptionRepository):
        self.service = AuthService(user_repo, subscription_repo)
    
    async def register(self, user_data: UserCreate) -> dict:
        """Register a new user"""
        result = await self.service.register(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
    
    async def login(self, email: str, password: str) -> dict:
        """Login a user"""
        result = await self.service.authenticate(email, password)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["message"]
            )
        
        user = result["data"]
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return {
            "status": RESPONSE_STATUS_SUCCESS,
            "message": "Login successful",
            "data": {
                "user": user,
                "access_token": access_token
            }
        }
    
    async def get_current_user(self, user_id: str) -> User:
        """Get current user"""
        user = await self.service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> dict:
        """Update user"""
        update_data = user_data.model_dump(exclude_unset=True)
        user = await self.service.update_user(user_id, update_data)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="User updated successfully",
            data=user
        )
    
    async def delete_user(self, user_id: str) -> dict:
        """Delete user"""
        deleted = await self.service.delete_user(user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="User deleted successfully",
            data=None
        )