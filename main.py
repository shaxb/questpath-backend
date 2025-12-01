from fastapi import FastAPI

app = FastAPI(title="QuestPath API", version="1.0.0")


# Include your routers here
from app.users import router as users_router
from app.goals import router as goals_router
from app.quizzes import router as quizzes_router
from app.progression import router as progression_router
from app.leaderboard import router as leaderboard_router


app.include_router(users_router)
app.include_router(goals_router)
app.include_router(quizzes_router)
app.include_router(progression_router)
app.include_router(leaderboard_router)