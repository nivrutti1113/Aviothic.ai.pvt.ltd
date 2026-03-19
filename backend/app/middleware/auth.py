import logging
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.requests import Request

from .auth import auth_service
from ..models.user import UserInDB, TokenData, UserRole

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer()


class AuthMiddleware:
    """Authentication middleware for medical AI platform.
    
    Medical audit compliant authentication with role-based access control.
    """
    
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> UserInDB:
        """Get current authenticated user from JWT token.
        
        Args:
            credentials: HTTP Bearer credentials containing JWT token
            
        Returns:
            Authenticated UserInDB object
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        token = credentials.credentials
        token_data = auth_service.decode_token(token)
        
        if not token_data or not token_data.user_id:
            logger.warning("Authentication failed: Invalid token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await auth_service.get_user_by_id(token_data.user_id)
        if not user:
            logger.warning(f"Authentication failed: User {token_data.user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(f"Authentication failed: User {user.email} is inactive")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user account",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"User {user.email} authenticated successfully")
        return user
    
    def require_roles(self, required_roles: List[UserRole]):
        """Dependency factory for role-based access control.
        
        Args:
            required_roles: List of roles that are allowed access
            
        Returns:
            Dependency function for role checking
        """
        async def role_checker(
            current_user: UserInDB = Depends(self.get_current_user)
        ) -> UserInDB:
            """Check if user has required role.
            
            Args:
                current_user: Authenticated user
                
            Returns:
                UserInDB object if authorized
                
            Raises:
                HTTPException: If user doesn't have required role
            """
            if current_user.role not in required_roles:
                logger.warning(
                    f"Authorization failed: User {current_user.email} "
                    f"(role: {current_user.role}) lacks required roles: {required_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            logger.debug(f"User {current_user.email} authorized with role {current_user.role}")
            return current_user
        
        return role_checker
    
    def get_current_active_user(
        self, 
        current_user: UserInDB = Depends(get_current_user)
    ) -> UserInDB:
        """Get current active user (dependency).
        
        Args:
            current_user: Authenticated user
            
        Returns:
            Active UserInDB object
            
        Raises:
            HTTPException: If user is inactive
        """
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return current_user


# Global auth middleware instance
auth_middleware = AuthMiddleware()

# Convenience dependencies
get_current_user = auth_middleware.get_current_user
get_current_active_user = auth_middleware.get_current_active_user

# Role-based dependencies
require_admin = auth_middleware.require_roles([UserRole.ADMIN])
require_doctor = auth_middleware.require_roles([UserRole.DOCTOR, UserRole.ADMIN])
require_any_role = auth_middleware.require_roles([UserRole.DOCTOR, UserRole.ADMIN])

__all__ = [
    "auth_middleware",
    "get_current_user", 
    "get_current_active_user",
    "require_admin",
    "require_doctor",
    "require_any_role"
]