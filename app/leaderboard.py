from fastapi import APIRouter, Depends, HTTPException




from app.auth import get_current_user
from app.db import get_db


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User
from app.schemas import LeaderboardResponse

from typing import Annotated



router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])
@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Retrieve the global leaderboard sorted by total experience points (XP).
    """
    result = await db.execute(
        select(
            User.id,
            User.email,
            User.total_exp
        ).order_by(User.total_exp.desc()).limit(10)
    )
    top_users = result.all()
    
    leaderboard = [
        {
            "rank": index + 1,
            "user_id": user.id,
            "email": user.email,
            "total_exp": user.total_exp
        }
        for index, user in enumerate(top_users)
    ]

    # calculate current user's rank
    result = await db.execute(
        select(User).order_by(User.total_exp.desc())
    )
    all_users = result.scalars().all()
    current_user_rank = next(
        (index + 1 for index, user in enumerate(all_users) if user.id == current_user.id),
        None
    )
    
    return {
        "leaderboard": leaderboard,
        "current_user": {
            "rank": current_user_rank,
            "user_id": current_user.id,
            "email": current_user.email,
            "total_exp": current_user.total_exp
        }
    }