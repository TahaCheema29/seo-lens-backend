from fastapi import HTTPException, status
from src.admin.auth.repository.admin_repository import AdminRepository
from src.models.user import Admin
from src.auth.schemas.user import AdminCreate, AdminUpdate
from src.core.security import get_password_hash, verify_password
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS, RESPONSE_STATUS_ERROR


class AdminAuthService:
    """Service for admin authentication operations"""
    
    def __init__(self, admin_repo: AdminRepository):
        self.admin_repo = admin_repo
    
    async def register(self, admin_data: AdminCreate) -> dict:
        """Register a new admin"""
        existing_admin = await self.admin_repo.get_by_email(admin_data.email)
        if existing_admin:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="Admin email already registered",
                data=None
            )
        
        hashed_password = get_password_hash(admin_data.password)
        
        admin = Admin(
            email=admin_data.email,
            hashed_password=hashed_password,
            full_name=admin_data.full_name,
            is_active=True,
            is_super_admin=False,
        )
        
        created_admin = await self.admin_repo.create(admin)
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Admin registered successfully",
            data=created_admin
        )
    
    async def authenticate(self, email: str, password: str) -> dict:
        """Authenticate an admin"""
        admin = await self.admin_repo.get_by_email(email)
        
        if not admin:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="Incorrect email or password",
                data=None
            )
        
        if not verify_password(password, admin.hashed_password):
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="Incorrect email or password",
                data=None
            )
        
        if not admin.is_active:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="Admin account is deactivated",
                data=None
            )
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Authentication successful",
            data=admin
        )
    
    async def get_all_admins(self, skip: int = 0, limit: int = 100) -> dict:
        """Get all admins"""
        admins = await self.admin_repo.get_all(skip, limit)
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Admins retrieved successfully",
            data=admins
        )
    
    async def get_admin_by_id(self, admin_id: str) -> dict:
        """Get admin by ID"""
        admin = await self.admin_repo.get_by_id(admin_id)
        if not admin:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="Admin not found",
                data=None
            )
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Admin retrieved successfully",
            data=admin
        )
    
    async def update_admin(self, admin_id: str, admin_data: AdminUpdate) -> dict:
        """Update admin information"""
        update_data = admin_data.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        elif "password" in update_data:
            del update_data["password"]
        
        admin = await self.admin_repo.update(admin_id, **update_data)
        
        if not admin:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="Admin not found",
                data=None
            )
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Admin updated successfully",
            data=admin
        )
    
    async def delete_admin(self, admin_id: str) -> dict:
        """Delete an admin"""
        deleted = await self.admin_repo.delete(admin_id)
        if not deleted:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="Admin not found",
                data=None
            )
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Admin deleted successfully",
            data=None
        )
    
    async def activate_admin(self, admin_id: str) -> dict:
        """Activate admin"""
        admin = await self.admin_repo.activate(admin_id)
        if not admin:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="Admin not found",
                data=None
            )
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Admin activated successfully",
            data=admin
        )
    
    async def deactivate_admin(self, admin_id: str) -> dict:
        """Deactivate admin"""
        admin = await self.admin_repo.deactivate(admin_id)
        if not admin:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="Admin not found",
                data=None
            )
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Admin deactivated successfully",
            data=admin
        )
    
    async def set_super_admin(self, admin_id: str, is_super: bool = True) -> dict:
        """Set super admin status"""
        admin = await self.admin_repo.set_super_admin(admin_id, is_super)
        if not admin:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message="Admin not found",
                data=None
            )
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Super admin status updated successfully",
            data=admin
        )