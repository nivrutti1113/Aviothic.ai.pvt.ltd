import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from bson import ObjectId

from ..config import settings
from ..models.user import UserInDB, UserCreate, UserLogin, TokenData, Token, UserRole
from ..db import db

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthService:
    """Production-ready authentication service for medical AI platform.
    
    Medical audit compliant with secure password handling and JWT tokens.
    Implements role-based access control for healthcare environment.
    """
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.secret_key = settings.SECRET_KEY
        if not self.secret_key or self.secret_key == "your_production_secret_key_here_change_this":
            raise ValueError("SECRET_KEY must be set in environment variables for production")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a plain password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token with expiration.
        
        Args:
            data: Token payload data
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user credentials.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            UserInDB object if authentication successful, None otherwise
        """
        try:
            user_doc = await db.db.users.find_one({"email": email.lower(), "is_active": True})
            if not user_doc:
                logger.warning(f"Authentication failed: User {email} not found or inactive")
                return None
                
            user = UserInDB(**user_doc)
            
            if not self.verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: Invalid password for user {email}")
                return None
            
            # Update last login timestamp
            await db.db.users.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            logger.info(f"User {email} authenticated successfully")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            return None
    
    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """Create a new user account.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created UserInDB object
            
        Raises:
            ValueError: If user already exists
        """
        # Check if user already exists
        existing_user = await db.db.users.find_one({"email": user_data.email.lower()})
        if existing_user:
            raise ValueError(f"User with email {user_data.email} already exists")
        
        # Hash password
        hashed_password = self.get_password_hash(user_data.password)
        
        # Create user document
        user_doc = {
            "_id": ObjectId(),
            "email": user_data.email.lower(),
            "full_name": user_data.full_name,
            "hospital": user_data.hospital,
            "hashed_password": hashed_password,
            "role": user_data.role.value,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        # Insert user
        result = await db.db.users.insert_one(user_doc)
        
        # Convert to UserInDB model
        user_doc["id"] = str(user_doc.pop("_id"))
        user = UserInDB(**user_doc)
        
        logger.info(f"Created new user: {user.email} with role {user.role}")
        return user
    
    def decode_token(self, token: str) -> Optional[TokenData]:
        """Decode JWT token and extract user data.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData object if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            
            if user_id is None or email is None:
                return None
                
            return TokenData(
                user_id=user_id,
                email=email,
                role=UserRole(role) if role else None
            )
            
        except JWTError as e:
            logger.warning(f"Token decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected token decode error: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID.
        
        Args:
            user_id: User ID string
            
        Returns:
            UserInDB object if found, None otherwise
        """
        try:
            user_doc = await db.db.users.find_one({"_id": ObjectId(user_id), "is_active": True})
            if not user_doc:
                return None
            
            user_doc["id"] = str(user_doc.pop("_id"))
            return UserInDB(**user_doc)
            
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {e}")
            return None
    
    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT refresh token with longer expiration.
        
        Args:
            data: Token payload data
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def create_token_response(self, user: UserInDB, include_refresh_token: bool = True) -> Dict[str, Any]:
        """Create token response for successful authentication.
        
        Args:
            user: Authenticated user
            include_refresh_token: Whether to include refresh token
            
        Returns:
            Token response dictionary with access and refresh tokens
        """
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value
            },
            expires_delta=access_token_expires
        )
        
        response = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
        if include_refresh_token:
            refresh_token_data = {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value
            }
            refresh_token = self.create_refresh_token(refresh_token_data)
            response["refresh_token"] = refresh_token
            
            # Update user's refresh tokens in database
            await db.db.users.update_one(
                {"_id": ObjectId(user.id)},
                {"$push": {"refresh_tokens": refresh_token}}
            )
        
        return response
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token string
            
        Returns:
            New token response if refresh token is valid, None otherwise
        """
        token_data = self.decode_token(refresh_token)
        if not token_data:
            return None
        
        # Check if refresh token exists in user's refresh_tokens list
        user = await self.get_user_by_id(token_data.user_id)
        if not user or not user.refresh_tokens or refresh_token not in user.refresh_tokens:
            return None
        
        # Get user details again to ensure they are still active
        user_doc = await db.db.users.find_one({"_id": ObjectId(token_data.user_id)})
        if not user_doc or not user_doc.get("is_active", True):
            return None
        
        # Create new tokens
        user = UserInDB(**user_doc)
        return await self.create_token_response(user, include_refresh_token=False)
    
    async def invalidate_refresh_token(self, refresh_token: str) -> bool:
        """Invalidate a refresh token by removing it from user's list.
        
        Args:
            refresh_token: Refresh token to invalidate
            
        Returns:
            True if token was successfully invalidated, False otherwise
        """
        # Find user who owns this refresh token
        user_doc = await db.db.users.find_one({"refresh_tokens": refresh_token})
        if not user_doc:
            return False
        
        # Remove the refresh token from the user's list
        await db.db.users.update_one(
            {"_id": user_doc["_id"]},
            {"$pull": {"refresh_tokens": refresh_token}}
        )
        
        return True
    
    async def initiate_forgot_password(self, email: str) -> bool:
        """Initiate forgot password process by generating a reset token.
        
        Args:
            email: User's email address
            
        Returns:
            True if the process was initiated successfully, False otherwise
        """
        import secrets
        import string
        
        user_doc = await db.db.users.find_one({"email": email.lower()})
        if not user_doc:
            return False
        
        # Generate a random token
        alphabet = string.ascii_letters + string.digits
        reset_token = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        # Set expiry time (1 hour from now)
        expiry_time = datetime.utcnow() + timedelta(hours=1)
        
        # Update user with reset token and expiry
        await db.db.users.update_one(
            {"_id": user_doc["_id"]},
            {
                "$set": {
                    "forgot_password_token": reset_token,
                    "forgot_password_expires": expiry_time
                }
            }
        )
        
        # In a real application, send email with reset_token here
        logger.info(f"Password reset initiated for user: {email}")
        return True
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using the forgot password token.
        
        Args:
            token: Password reset token
            new_password: New password to set
            
        Returns:
            True if password was reset successfully, False otherwise
        """
        # Find user with the given token
        user_doc = await db.db.users.find_one({"forgot_password_token": token})
        if not user_doc:
            logger.warning(f"Invalid or expired password reset token")
            return False
        
        # Check if token has expired
        if user_doc.get("forgot_password_expires") < datetime.utcnow():
            logger.warning(f"Password reset token has expired")
            # Clean up expired token
            await db.db.users.update_one(
                {"_id": user_doc["_id"]},
                {"$unset": {"forgot_password_token": "", "forgot_password_expires": ""}}
            )
            return False
        
        # Hash new password
        hashed_password = self.get_password_hash(new_password)
        
        # Update user's password and clear reset token
        await db.db.users.update_one(
            {"_id": user_doc["_id"]},
            {
                "$set": {"hashed_password": hashed_password},
                "$unset": {"forgot_password_token": "", "forgot_password_expires": ""}
            }
        )
        
        logger.info(f"Password reset successful for user: {user_doc['email']}")
        return True


# Global auth service instance
auth_service = AuthService()

__all__ = ["auth_service", "AuthService"]