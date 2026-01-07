from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated

from app.ai_service import generate_quiz_for_level

from app.schemas import QuizSubmitRequest, QuizResultResponse
from app.models import Level, Roadmap, Goal, User, LevelStatus, GoalStatus
from app.config import settings

router = APIRouter(prefix="/levels", tags=["levels"])


@router.get("/{level_id}/quiz")
async def get_level_quiz(
    level_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    result = await db.execute(
        select(Level)
        .join(Roadmap, Level.roadmap_id == Roadmap.id)
        .join(Goal, Roadmap.goal_id == Goal.id)
        .where(Level.id == level_id, Goal.user_id == current_user.id)
    )
    level = result.scalars().first()
    if not level:
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
        
        # Add level info and time limit
        response = {
            "level_id": level.id,
            "level_title": level.title,
            "time_limit": 300,  # 5 minutes
            "questions": quiz_data["questions"]
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






@router.post("/{level_id}/quiz/submit")
async def submit_level_quiz(
    level_id: int,
    quiz_submit: QuizSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    result = await db.execute(
        select(Level)
        .join(Roadmap, Level.roadmap_id == Roadmap.id)
        .join(Goal, Roadmap.goal_id == Goal.id)
        .where(Level.id == level_id, Goal.user_id == current_user.id)
    )
    level = result.scalars().first()
    if not level:
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
   
        # change goal status to in progress or completed
        goal_result = await db.execute(
            select(Goal)
            .join(Roadmap, Goal.id == Roadmap.goal_id)
            .join(Level, Roadmap.id == Level.roadmap_id)
            .where(Level.id == level.id)
        )
        goal = goal_result.scalars().first()
        if goal:
            # Check if all levels in the roadmap are completed
            levels_result = await db.execute(
                select(Level)
                .where(Level.roadmap_id == level.roadmap_id)
            )
            levels = levels_result.scalars().all()
            if all(l.status == LevelStatus.COMPLETED for l in levels):
                goal.status = GoalStatus.COMPLETED
            else:
                goal.status = GoalStatus.IN_PROGRESS

        # Unlock next level
        next_level_result = await db.execute(
            select(Level)
            .where(
                Level.roadmap_id == level.roadmap_id,
                Level.order == level.order + 1
            )
        )
        next_level = next_level_result.scalars().first()
        
        if next_level and next_level.status == LevelStatus.LOCKED:
            next_level.status = LevelStatus.UNLOCKED
            next_level_unlocked = True
            message = f"Congratulations! You earned {xp_earned} XP and unlocked the next level!"
        else:
            message = f"Congratulations! You earned {xp_earned} XP!"
        
        await db.commit()
    else:
        message = "You didn't pass this time. Review the topics and try again!"
    
    return {
        "passed": quiz_submit.passed,
        "xp_earned": xp_earned,
        "next_level_unlocked": next_level_unlocked,
        "message": message
    }

