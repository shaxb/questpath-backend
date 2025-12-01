from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Annotated

# Import necessary modules and functions
from .db import get_db
from .models import User
from .auth import hash_password, verify_password, create_access_token, get_current_user
from .schemas import RegisterRequest, UserResponse, TokenResponse



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
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # find the user by email (OAuth2 sends 'username', we treat it as email)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_my_info(current_user: User = Depends(get_current_user)):
    return current_user
