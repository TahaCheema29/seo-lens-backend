from src.auth.repository.user_repository import UserRepository
from src.models.user import User, UserRole
from src.core.security import get_password_hash, verify_password
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS, RESPONSE_STATUS_ERROR


class AuthService:
    """Service for user authentication operations"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def register(self, email: str, password: str, full_name: str = None) -> dict:
        """Register a new user"""
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="Email already registered",
                data=None
            )
        
        hashed_password = get_password_hash(password)
        
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=UserRole.USER,
            is_active=True,
        )
        
        created_user = await self.user_repo.create(user)
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="User registered successfully",
            data=created_user
        )
    
    async def authenticate(self, email: str, password: str) -> dict:
        """Authenticate a user"""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="Incorrect email or password",
                data=None
            )
        
        if not verify_password(password, user.hashed_password):
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="Incorrect email or password",
                data=None
            )
        
        if not user.is_active:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="User account is deactivated",
                data=None
            )
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Authentication successful",
            data=user
        )
    
    async def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID"""
        user = await self.user_repo.get_by_id(user_id)
        return user
    
    async def update_user(self, user_id: str, update_data: dict) -> User:
        """Update user information"""
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        elif "password" in update_data:
            del update_data["password"]
        
        user = await self.user_repo.update(user_id, **update_data)
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        deleted = await self.user_repo.delete(user_id)
        return deleted