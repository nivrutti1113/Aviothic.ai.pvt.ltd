import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from ..models.user import UserCreate, UserLogin, UserResponse, Token
from ..services.auth import auth_service
from ..middleware.auth import get_current_user
from ..models.user import UserInDB

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", 
             response_model=UserResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Register new user account",
             description="""Register a new user account in the medical AI platform.
             
             Medical audit compliant user registration with role-based access control.
             Only administrators can create accounts in production environments.
             """)
async def register_user(user_data: UserCreate):
    """Register a new user account.
    
    Args:
        user_data: User registration data
        
    Returns:
        Created user information (password excluded)
        
    Raises:
        HTTPException: If user already exists or validation fails
    """
    try:
        logger.info(f"Creating new user account for: {user_data.email}")
        
        # Create user through auth service
        user = await auth_service.create_user(user_data)
        
        # Return response without sensitive data
        response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            hospital=user.hospital,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )
        
        logger.info(f"User account created successfully: {user.email}")
        return response
        
    except ValueError as e:
        logger.warning(f"User registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during user registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/login",
             response_model=Token,
             summary="Authenticate user and get access token",
             description="""Authenticate user credentials and return JWT access token.
             
             Medical audit compliant authentication with secure token generation.
             Tokens expire after 30 minutes for security.
             """)
async def login_user(user_credentials: UserLogin):
    """Authenticate user and return access token.
    
    Args:
        user_credentials: User email and password
        
    Returns:
        JWT access token and metadata
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        logger.info(f"Login attempt for user: {user_credentials.email}")
        
        # Authenticate user
        user = await auth_service.authenticate_user(
            user_credentials.email, 
            user_credentials.password
        )
        
        if not user:
            logger.warning(f"Login failed for user: {user_credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create token response
        token_response = await auth_service.create_token_response(user)
        
        logger.info(f"User {user.email} logged in successfully")
        return token_response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/me",
            response_model=UserResponse,
            summary="Get current user information",
            description="""Get information about the currently authenticated user.
            
            Medical audit compliant user information endpoint.
            Requires valid authentication token.
            """)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user)):
    """Get current authenticated user information.
    
    Args:
        current_user: Authenticated user (from dependency)
        
    Returns:
        Current user information (password excluded)
    """
    logger.debug(f"Retrieving user info for: {current_user.email}")
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        hospital=current_user.hospital,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/logout",
             summary="Logout user (token invalidation)",
             description="""Invalidate current user session.
             
             Note: JWT tokens cannot be truly invalidated server-side.
             This endpoint is for audit logging purposes.
             Client should delete the token locally.
             """)
async def logout_user(current_user: UserInDB = Depends(get_current_user)):
    """Logout user (audit logging).
    
    Args:
        current_user: Authenticated user (from dependency)
        
    Returns:
        Success message
    """
    logger.info(f"User {current_user.email} logged out")
    
    # Note: In a real production system, you might want to implement
    # token blacklisting using Redis or similar for true logout functionality
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Successfully logged out"}
    )


@router.post("/refresh",
             summary="Refresh access token using refresh token",
             description="""Refresh the access token using a valid refresh token.
             
             Production-ready refresh token implementation with proper validation.
             """)
async def refresh_token(refresh_token_request: dict):
    """Refresh access token using refresh token.
    
    Args:
        refresh_token_request: Contains the refresh token
        
    Returns:
        New access token and refresh token
    """
    refresh_token = refresh_token_request.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required"
        )
    
    try:
        token_response = await auth_service.refresh_access_token(refresh_token)
        
        if not token_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info("Access token refreshed successfully")
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/forgot-password",
             summary="Initiate forgot password process",
             description="""Start the forgot password process by sending a reset token to the user.
             
             This endpoint initiates the password reset flow by generating a reset token.
             In a real application, this would send an email to the user.
             """)
async def forgot_password(email_request: dict):
    """Initiate forgot password process.
    
    Args:
        email_request: Contains the user's email address
        
    Returns:
        Success message if the process was initiated
    """
    email = email_request.get("email")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    try:
        success = await auth_service.initiate_forgot_password(email)
        
        if success:
            logger.info(f"Password reset process initiated for email: {email}")
            return {"message": "If an account exists with this email, a reset link has been sent"}
        else:
            # Still return the same response to prevent email enumeration
            logger.info(f"Password reset process attempted for non-existent email: {email}")
            return {"message": "If an account exists with this email, a reset link has been sent"}
            
    except Exception as e:
        logger.error(f"Unexpected error during forgot password process: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/reset-password",
             summary="Reset password using reset token",
             description="""Reset the user's password using the forgot password token.
             
             Validates the reset token and sets the new password if valid.
             """)
async def reset_password(reset_request: dict):
    """Reset password using reset token.
    
    Args:
        reset_request: Contains the reset token and new password
        
    Returns:
        Success message if the password was reset
    """
    token = reset_request.get("token")
    new_password = reset_request.get("new_password")
    
    if not token or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token and new password are required"
        )
    
    # Basic password validation
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    try:
        success = await auth_service.reset_password(token, new_password)
        
        if success:
            logger.info("Password reset successfully")
            return {"message": "Password reset successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during password reset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


__all__ = ["router"]