from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON
from app.db import Base
import enum


# Enums
class GoalStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class DifficultyLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LevelStatus(enum.Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# Models
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    total_exp: Mapped[int] = mapped_column(Integer, default=0)

    # Relationship (NOT a database column)
    goals: Mapped[list["Goal"]] = relationship("Goal", back_populates="user")


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    # AI-generated fields
    title: Mapped[str] = mapped_column(String(200), nullable=False)  # AI-cleaned title
    description: Mapped[str] = mapped_column(Text, nullable=False)  # User's original goal text
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # AI-d`1etermined category
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(nullable=False)
    
    status: Mapped[GoalStatus] = mapped_column(default=GoalStatus.NOT_STARTED)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="goals")
    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="goal", uselist=False)


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), unique=True, nullable=False)
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    goal: Mapped["Goal"] = relationship("Goal", back_populates="roadmap")
    levels: Mapped[list["Level"]] = relationship("Level", back_populates="roadmap", order_by="Level.order")


class Level(Base):
    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    roadmap_id: Mapped[int] = mapped_column(ForeignKey("roadmaps.id"), nullable=False, index=True)
    
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    topics: Mapped[list] = mapped_column(JSON, nullable=True)  # Array of {"name": str, "completed": bool}
    xp_reward: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[LevelStatus] = mapped_column(default=LevelStatus.LOCKED)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="levels")



