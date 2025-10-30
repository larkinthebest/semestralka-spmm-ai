from datetime import datetime, timedelta
from typing import Optional
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
import httpx
import os

# IMPORTANT: For production, use a strong, randomly generated key stored securely (e.g., environment variable).
# For development, we'll use a fixed key for consistency.
SECRET_KEY = "super-secret-dev-key-please-change-in-production-environment" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 240 # Increased to 4 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Truncate password to 72 bytes for bcrypt compatibility
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    print(f"DEBUG: Received token for verification: {credentials.credentials[:30]}...") # Log token snippet
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            print("DEBUG: Token payload missing 'sub' (email).")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials: Missing email in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        print(f"DEBUG: Token validated for email: {email}")
        return email
    except InvalidTokenError as e:
        print(f"DEBUG: Invalid token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: Invalid token ({e})",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"DEBUG: Unexpected error during token verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: Unexpected error ({e})",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(email: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def verify_google_token(token: str) -> dict:
    """Verify Google OAuth token and return user info"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={token}"
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=401, detail="Invalid Google token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Failed to verify Google token")

def create_or_get_google_user(user_info: dict, db: Session) -> User:
    """Create or get user from Google OAuth info"""
    email = user_info.get("email")
    name = user_info.get("name", email.split("@")[0])
    
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create new user
        user = User(
            email=email,
            username=name,
            hashed_password="",  # No password for OAuth users
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)), db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user but return None if not authenticated (for guest access)"""
    if not credentials:
        print("DEBUG: No credentials provided for optional user.")
        return None
    
    print(f"DEBUG: Received optional token for verification: {credentials.credentials[:30]}...") # Log token snippet
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            print("DEBUG: Optional token payload missing 'sub' (email).")
            return None
        
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            print(f"DEBUG: User not found for email from optional token: {email}")
        return user
    except InvalidTokenError as e:
        print(f"DEBUG: Invalid optional token error: {e}")
        return None
    except Exception as e:
        print(f"DEBUG: Unexpected error during optional token verification: {e}")
        return None
