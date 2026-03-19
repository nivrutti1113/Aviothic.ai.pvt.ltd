from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from enum import Enum
from datetime import datetime


class UserRole(str, Enum):
    """User roles for role-based access control.
    
    Medical audit compliant role definitions.
    """
    USER = "user"
    DOCTOR = "doctor"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user model for request/response validation."""
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., description="User full name")
    hospital: Optional[str] = Field(None, description="Hospital affiliation")


class UserCreate(UserBase):
    """User creation request model."""
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    role: UserRole = Field(UserRole.USER, description="User role")


class UserLogin(BaseModel):
    """User login request model."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class UserInDB(UserBase):
    """User model as stored in database."""
    id: str = Field(..., description="User ID")
    hashed_password: str = Field(..., description="Hashed password")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(True, description="Account status")
    refresh_tokens: Optional[List[str]] = Field(None, description="List of refresh tokens")
    forgot_password_token: Optional[str] = Field(None, description="Forgot password token")
    forgot_password_expires: Optional[datetime] = Field(None, description="Forgot password token expiry")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")


class UserResponse(UserBase):
    """User response model (safe for API responses)."""
    id: str = Field(..., description="User ID")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Account status")
    created_at: datetime = Field(..., description="Account creation timestamp")


class Token(BaseModel):
    """JWT token response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None


# Export all models
__all__ = [
    "UserRole",
    "UserBase", 
    "UserCreate",
    "UserLogin",
    "UserInDB",
    "UserResponse",
    "Token",
    "TokenData"
]