from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


from app.auth import get_current_user
from app.db import get_db
from app.cache import get_cache, set_cache
from app.models import User
from app.schemas import LeaderboardResponse
from app.rate_limiter import check_rate_limit
from .logger import logger


router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)], 
    current_user: Annotated[User, Depends(get_current_user)]
):
    
    """
    Retrieve the global leaderboard sorted by total experience points (XP).
    """
    # Rate limiting: 20 requests per minute (cached, can be lenient)
    await check_rate_limit(request, "get_leaderboard", limit=20, window=40)
    
    leaderboard = []

    # check redis cache first
    cached_leaderboard = get_cache("leaderboard")
    if cached_leaderboard:
        leaderboard = json.loads(cached_leaderboard)
    else:
        # fetch top 10 users by total_exp
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
        # cache the leaderboard for 5 minutes
        set_cache("leaderboard", json.dumps(leaderboard), expire=300)

    # calculate current user's rank
    rank_result = await db.execute(
        select(func.rank().over(order_by=User.total_exp.desc()).label("rank"),
            User.id
        ).where(User.id == current_user.id)
    )

    current_user_rank_row = rank_result.first()
    current_user_rank = current_user_rank_row.rank if current_user_rank_row else None
    
    return {
        "leaderboard": leaderboard,
        "current_user": {
            "rank": current_user_rank,
            "user_id": current_user.id,
            "email": current_user.email,
            "total_exp": current_user.total_exp
        }
    }