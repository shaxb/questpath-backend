from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_user
from app.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated
from sqlalchemy.orm import selectinload


from app.ai_service import generate_quiz_for_level
from app.schemas import QuizSubmitRequest
from app.models import Level, Roadmap, Goal, User, LevelStatus, GoalStatus
from app.cache import delete_cache
from app.rate_limiter import check_rate_limit
from .logger import logger
from .metrics import metrics

router = APIRouter(prefix="/levels", tags=["levels"])

# Endpoint to generate and retrieve quiz for a specific level
@router.get("/{level_id}/quiz")
async def get_level_quiz(
    request: Request,
    level_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    # Rate limiting: 10 quiz generations 6 minutes (AI generation is expensive)
    await check_rate_limit(request, "generate_quiz", limit=10, window=360)
    
    result = await db.execute(
        select(Level)
        .join(Roadmap, Level.roadmap_id == Roadmap.id)
        .join(Goal, Roadmap.goal_id == Goal.id)
        .where(Level.id == level_id, Goal.user_id == current_user.id)
    )
    level = result.scalars().first()
    if not level:
        logger.error("Level not found for quiz generation", level_id=level_id, user_id=current_user.id, event="level_not_found_quiz")
        raise HTTPException(status_code=404, detail="Level not found")
    
    # Check if all topics are completed before allowing quiz
    if level.topics and not all(topic.get("completed", False) for topic in level.topics):
        raise HTTPException(
            status_code=403, 
            detail="Complete all topics before taking the quiz"
        )
    
    # Generate quiz for the level based on its topics
    try:
        quiz_data = await generate_quiz_for_level(level.title, level.topics or [])
        
        # Track business metric
        metrics.increment_business_metric("quizzes_generated")
        
        # Add level info and time limit
        response = {
            "level_id": level.id,
            "level_title": level.title,
            "time_limit": 300,  # 5 minutes # depricated, handled on frontend
            "questions": quiz_data["questions"]
        }
        
        return response
    except Exception as e:
        logger.error("Failed to generate quiz", level_id=level_id, error=str(e), event="quiz_generation_failed")
        raise HTTPException(status_code=500, detail=str(e))





# submit quiz answers for a specific level
@router.post("/{level_id}/quiz/submit")
async def submit_level_quiz(
    request: Request,
    level_id: int,
    quiz_submit: QuizSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    # Rate limiting: 20 quiz submissions per 2 minutes
    await check_rate_limit(request, "submit_quiz", limit=20, window=120)
    
    # ✅ OPTIMIZED: Load level with ALL related data in one go
    result = await db.execute(
        select(Level)
        .options(
            selectinload(Level.roadmap).selectinload(Roadmap.goal),    # Load roadmap → goal
            selectinload(Level.roadmap).selectinload(Roadmap.levels)   # Load roadmap → all levels
        )
        .join(Roadmap, Level.roadmap_id == Roadmap.id)
        .join(Goal, Roadmap.goal_id == Goal.id)
        .where(Level.id == level_id, Goal.user_id == current_user.id)
    )

    level = result.scalar_one_or_none()

    if not level:
        logger.error("Level not found for quiz submission", level_id=level_id, user_id=current_user.id, event="level_not_found_quiz_submit")
        raise HTTPException(status_code=404, detail="Level not found")
    
    # Initialize response values
    xp_earned = 0
    next_level_unlocked = False
    message = ""
    
    if quiz_submit.passed:
        # Award XP if passed (full XP reward)
        xp_earned = level.xp_reward

        # Update user's total XP
        current_user.total_exp += xp_earned
        
        # Mark level as completed if not already
        from app.models import LevelStatus
        if level.status != LevelStatus.COMPLETED:
            level.status = LevelStatus.COMPLETED
   
        # ✅ OPTIMIZED: Use pre-loaded data (no additional queries!)
        goal = level.roadmap.goal  # Already loaded via selectinload
        all_levels = level.roadmap.levels  # Already loaded via selectinload
        
        # Check if all levels in the roadmap are completed
        if all(l.status == LevelStatus.COMPLETED for l in all_levels):
            goal.status = GoalStatus.COMPLETED
        else:
            goal.status = GoalStatus.IN_PROGRESS

        # Find next level (no query needed!)
        next_level = next((l for l in all_levels if l.order == level.order + 1), None)
        
        if next_level and next_level.status == LevelStatus.LOCKED:
            next_level.status = LevelStatus.UNLOCKED
            next_level_unlocked = True
            message = f"Congratulations! You earned {xp_earned} XP and unlocked the next level!"
        else:
            message = f"Congratulations! You earned {xp_earned} XP!"
        
        # Clear relevant caches
        delete_cache("leaderboard")
        
        # Track business metric
        metrics.increment_business_metric("quizzes_completed")

        await db.commit()
    else:
        message = "You didn't pass this time. Review the topics and try again!"
    
    return {
        "passed": quiz_submit.passed,
        "xp_earned": xp_earned,
        "next_level_unlocked": next_level_unlocked,
        "message": message
    }

