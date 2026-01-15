from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from typing import Annotated, List

from .db import get_db
from .models import User, Goal, Roadmap, Level, GoalStatus, DifficultyLevel, LevelStatus
from .schemas import CreateGoalRequest, GoalResponse, GoalListItem
from .auth import get_current_user
from .ai_service import generate_roadmap
from .rate_limiter import check_rate_limit
from .logger import logger
from .metrics import metrics

router = APIRouter(prefix="/goals", tags=["goals"])

# Endpoint to create a new goal with AI-generated roadmap
@router.post("", response_model=GoalResponse, status_code=201)
async def create_goal(
    request: Request,
    incoming_request: CreateGoalRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Create a new goal with AI-generated roadmap.
    
    1. User sends goal description
    2. AI generates structured roadmap
    3. Store Goal + Roadmap + Levels in database
    4. Return complete goal with roadmap
    """
    # Rate limiting: 5 goals per hour (AI generation is expensive)
    await check_rate_limit(request, "create_goal", limit=5, window=360)
    
    try:
        # Step 1: Generate roadmap using AI
        ai_data = await generate_roadmap(incoming_request.description)
        
        # Step 2: Create Goal
        goal = Goal(
            user_id=current_user.id,
            title=ai_data["title"],
            description=incoming_request.description,
            category=ai_data["category"],
            difficulty_level=DifficultyLevel(ai_data["difficulty"]),
            status=GoalStatus.NOT_STARTED
        )
        db.add(goal)
        await db.flush()  # Get goal.id
        
        # Step 3: Create Roadmap
        roadmap = Roadmap(
            goal_id=goal.id,
            name=ai_data["roadmap"]["name"]
        )
        db.add(roadmap)
        await db.flush()  # Get roadmap.id
        
        # Step 4: Create Levels
        for level_data in ai_data["roadmap"]["levels"]:
            level = Level(
                roadmap_id=roadmap.id,
                order=level_data["order"],
                title=level_data["title"],
                description=level_data["description"],
                topics=level_data["topics"],
                xp_reward=level_data["xp_reward"],
                status=LevelStatus.UNLOCKED if level_data["order"] == 1 else LevelStatus.LOCKED
            )
            db.add(level)
        
        await db.commit()
        
        # Step 5: Refresh and load relationships
        await db.refresh(goal)
        result = await db.execute(
            select(Goal)
            .options(selectinload(Goal.roadmap).selectinload(Roadmap.levels))
            .where(Goal.id == goal.id)
        )
        goal = result.scalar_one()
        
        # Track business metric
        metrics.increment_business_metric("goals_created")
        
        return goal
        
    except ValueError as e:
        # AI validation errors
        logger.error("Invalid goal data from AI", error=str(e), event="invalid_goal_data")
        raise HTTPException(status_code=400, detail=f"Invalid goal: {str(e)}")
    except Exception as e:
        # Other errors (OpenAI API, database, etc.)
        logger.error("Failed to create goal", error=str(e), event="goal_creation_error")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create goal: {str(e)}")



# Endpoint to get all goals for the current user (without roadmap details)
@router.get("/me", response_model=List[GoalListItem])
async def get_my_goals(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get all goals for the current user (without roadmap details for performance).
    """
    result = await db.execute(
        select(Goal)
        .where(Goal.user_id == current_user.id)
        .order_by(Goal.created_at.desc())
    )
    goals = result.scalars().all()
    return goals

# Endpoint to get a specific goal with full roadmap and levels
@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get a specific goal with full roadmap and levels.
    """
    result = await db.execute(
        select(Goal)
        .options(selectinload(Goal.roadmap).selectinload(Roadmap.levels))
        .where(Goal.id == goal_id, Goal.user_id == current_user.id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        logger.error("Goal not found", goal_id=goal_id, user_id=current_user.id, event="goal_not_found")
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return goal


# Additional endpoints for updating goal status
@router.patch("/levels/{level_id}/topics/{topic_index}")
async def mark_topic(
    level_id: int,
    topic_index: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Mark a specific topic within a level as completed.
    """
    # Fetch the level and associated goal to verify ownership
    result = await db.execute(
        select(Level)
        .join(Roadmap, Level.roadmap_id == Roadmap.id)
        .join(Goal, Roadmap.goal_id == Goal.id)
        .where(Level.id == level_id, Goal.user_id == current_user.id)
    )
    level = result.scalar_one_or_none()
    
    if not level:
        logger.error("Level not found for marking topic", level_id=level_id, user_id=current_user.id, event="level_not_found")
        raise HTTPException(status_code=404, detail="Level not found")
    
    # Update the topic's completed status
    if level.topics is None or topic_index < 0 or topic_index >= len(level.topics):
        logger.error("Invalid topic index for marking topic", level_id=level_id, topic_index=topic_index, event="invalid_topic_index")
        raise HTTPException(status_code=400, detail="Invalid topic index")
    
    level.topics[topic_index]["completed"] = not level.topics[topic_index]["completed"]
    flag_modified(level, "topics")  # Tell SQLAlchemy that topics changed
    
    await db.commit()
    return {"detail": "Topic marked as completed"}
