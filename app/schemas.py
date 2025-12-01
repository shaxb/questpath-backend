from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import GoalStatus, DifficultyLevel, LevelStatus


class RegisterRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ===== Goal Schemas =====

class CreateGoalRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=500, description="Your learning goal")


class TopicResponse(BaseModel):
    """Individual topic within a level"""
    name: str
    completed: bool = False


class LevelResponse(BaseModel):
    id: int
    order: int
    title: str
    description: Optional[str]
    topics: Optional[List[TopicResponse]] = []
    xp_reward: int
    status: LevelStatus
    
    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    id: int
    name: str
    levels: List[LevelResponse]
    
    class Config:
        from_attributes = True


class GoalResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    difficulty_level: DifficultyLevel
    status: GoalStatus
    created_at: datetime
    roadmap: Optional[RoadmapResponse] = None
    
    class Config:
        from_attributes = True


class GoalListItem(BaseModel):
    """Simplified goal for list view (no roadmap details)"""
    id: int
    title: str
    category: str
    difficulty_level: DifficultyLevel
    status: GoalStatus
    created_at: datetime
    
    class Config:
        from_attributes = True



# ===== Quiz Schemas =====

class QuizOption(BaseModel):
    """Single option for a multiple choice question"""
    text: str
    value: str  # A, B, C, or D


class QuizQuestion(BaseModel):
    """Single quiz question with options and correct answer"""
    id: int
    question: str
    options: List[QuizOption]
    correct_answer: str  # A, B, C, or D


class QuizResponse(BaseModel):
    """Complete quiz data sent to frontend"""
    level_id: int
    level_title: str
    time_limit: int  # seconds
    questions: List[QuizQuestion]


class QuizSubmitRequest(BaseModel):
    """Quiz submission from frontend"""
    score: int = Field(..., ge=0, le=100, description="Score percentage")
    passed: bool
    time_taken: int = Field(..., ge=0, description="Time taken in seconds")


class QuizResultResponse(BaseModel):
    """Result after quiz submission"""
    passed: bool
    xp_earned: int
    next_level_unlocked: bool
    message: str




# leaderboard schemas


class Leaderboardcondidate(BaseModel):
    rank: int
    user_id: int
    email: str
    total_exp: int

    class Config:
        from_attributes = True

class LeaderboardResponse(BaseModel):
    leaderboard: List[Leaderboardcondidate]
    current_user: Leaderboardcondidate



# progress schemas

class StatsResponse(BaseModel):
    total_exp: int
    levels_completed: int
    goal_completion_percentage: int





