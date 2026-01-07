from passlib.context import CryptContext
from fastapi import Depends, HTTPException
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)



def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Hash refresh tokens for db storage
def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()




# JWT related functions would go here
from datetime import datetime, timedelta, timezone
from jose import jwt
from .config import settings

def create_access_token(data: dict):
    return _create_token(data, expires_delta=timedelta(minutes=settings.access_token_expire_minutes))



def create_refresh_token(data: dict):
    return _create_token(data, expires_delta=timedelta(minutes=settings.refresh_token_expire_minutes))



def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def _create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    if "sub" not in to_encode:
        raise ValueError("Token payload must contain 'sub' field")
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt

# OAuth2 would go here
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from .db import get_db
from .models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db:Annotated[AsyncSession, Depends(get_db)]) -> User:
    payload = decode_token(token)
    id: str = payload.get("sub")
    if id is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    user = await db.get(User, int(id))
    if user is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user