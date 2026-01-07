from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user
from app.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated
from app.models import User, Goal, Level, Roadmap, LevelStatus
from sqlalchemy import func
from app.schemas import StatsResponse




router = APIRouter(prefix="/progression", tags=["progression"])
@router.get("/stats", response_model=StatsResponse)
async def get_user_progression(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated["User", Depends(get_current_user)]
):
    """
    Retrieve user's progression statistics including total XP, levels completed, and goals achieved.
    """
    # Fetch total XP from user
    total_xp = current_user.total_exp

    # Count completed levels
    result = await db.execute(
        select(func.count())
        .select_from(Level)
        .join(Roadmap, Level.roadmap_id == Roadmap.id)
        .join(Goal, Roadmap.goal_id == Goal.id)
        .where(
            Goal.user_id == current_user.id,
            Level.status == LevelStatus.COMPLETED
        )
    )
    levels_completed = result.scalar_one()
    
    # Count total levels for progression percentage
    result = await db.execute(
        select(func.count())
        .select_from(Level)
        .join(Roadmap, Level.roadmap_id == Roadmap.id)
        .join(Goal, Roadmap.goal_id == Goal.id)
        .where(Goal.user_id == current_user.id)
    )
    total_levels = result.scalar_one()

    return StatsResponse(
        email=current_user.email,
        display_name=current_user.display_name,
        profile_picture=current_user.profile_picture,
        total_exp=total_xp,
        levels_completed=levels_completed,
        goal_completion_percentage=int(levels_completed / total_levels * 100) if total_levels > 0 else 0
    )
