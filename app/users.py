from fastapi import Depends, HTTPException, APIRouter, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from typing import Annotated
from datetime import datetime, timezone

# Import necessary modules and functions
from .db import get_db
from .models import User
from .auth import hash_password, verify_password, create_access_token, get_current_user, create_refresh_token, hash_refresh_token, decode_token
from .schemas import RegisterRequest, UserResponse, TokenResponse, OAuthLoginRequest, UpdateProfileRequest
from .config import settings


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user_req: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_req.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # hash the password
    password_hash = hash_password(user_req.password)

    # Create new user instance
    new_user = User(email=user_req.email, password_hash=password_hash)

    # Add and commit the new user to the database
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # find the user by email (OAuth2 sends 'username', we treat it as email)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    # generate refresh token
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # set refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.refresh_token_expire_minutes * 60
    )

    # add refresh token hash to db
    user.refresh_token_hash = hash_refresh_token(refresh_token)
    await db.commit()

    return TokenResponse(access_token=access_token)

# refresh to get new access token
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,  # Changed from Response - need Request to read cookies
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # get refresh token from cookies
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    
    # decode and validate refresh token (automatically checks exp)
    payload = decode_token(refresh_token)  # This already checks expiration!
    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # get user from db and verify token hash
    user = await db.get(User, int(user_id))
    if not user or user.refresh_token_hash != hash_refresh_token(refresh_token):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # create new access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=access_token)

@router.get("/me", response_model=UserResponse)
async def get_my_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    update_req: UpdateProfileRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Update user profile (display name)"""
    if update_req.display_name is not None:
        current_user.display_name = update_req.display_name
        await db.commit()
        await db.refresh(current_user)
    
    return current_user


@router.post("/oauth-login", response_model=TokenResponse)
async def oauth_login(
    oauth_req: OAuthLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Handle OAuth login from NextAuth.
    Frontend sends user info from Google OAuth, we trust it (NextAuth verified it).
    Find or create user, return our JWT token.
    """
    # Find user by email or google_id
    result = await db.execute(
        select(User).where(
            or_(User.email == oauth_req.email, User.google_id == oauth_req.google_id)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user (no password needed for OAuth!)
        user = User(
            email=oauth_req.email,
            google_id=oauth_req.google_id,
            display_name=oauth_req.display_name,
            profile_picture=oauth_req.profile_picture,
            password_hash=None  # OAuth users don't have passwords
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update existing user's OAuth info if needed
        if not user.google_id:
            user.google_id = oauth_req.google_id
        if oauth_req.display_name:
            user.display_name = oauth_req.display_name
        if oauth_req.profile_picture:
            user.profile_picture = oauth_req.profile_picture
        await db.commit()
    
    # Create our JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(access_token=access_token)
