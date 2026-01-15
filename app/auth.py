from passlib.context import CryptContext
from fastapi import Depends, HTTPException
import hashlib
from app.logger import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# hash password with salt for db storage
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# verify password against hashed version 
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)



# Hash refresh tokens for db storage
def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()




# JWT related functions go here
from datetime import datetime, timedelta, timezone
from jose import jwt, ExpiredSignatureError
from .config import settings

# Create access. 
def create_access_token(data: dict):
    return _create_token(data, expires_delta=timedelta(minutes=settings.access_token_expire_minutes))

# Create refresh token
def create_refresh_token(data: dict):
    return _create_token(data, expires_delta=timedelta(minutes=settings.refresh_token_expire_minutes))


# Decode token from incoming request
def decode_token(token: str):
    """
    Decode and validate a JWT token.
    Raises HTTPException if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except ExpiredSignatureError:
        logger.debug("Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError as e:
        logger.error("Token decoding fails", error=str(e), event="token_decode_error")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# Internal function to create JWT tokens
def _create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    if "sub" not in to_encode:
        logger.error("Token payload missing 'sub' field")
        raise ValueError("Token payload must contain 'sub' field")
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


# Dependency to get current user from token
# OAuth2 go here
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from .db import get_db
from .models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependency to get current user from token
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db:Annotated[AsyncSession, Depends(get_db)]) -> User:
    payload = decode_token(token)
    id: str = payload.get("sub")
    if id is None:
        logger.error("Token payload missing 'sub' field")
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    user = await db.get(User, int(id))
    if user is None:
        logger.error("User not found for given token", user_id=id, event="user_not_found")
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user