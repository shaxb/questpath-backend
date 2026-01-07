from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="QuestPath API", version="1.0.0")

# CORS middleware - allows frontend to call API
allowed_origins = [
    "http://localhost:3000",  # Local development
    "http://localhost:3001",  # Alternate port
    settings.frontend_url,     # Production frontend (Vercel)
]

# Remove duplicates and empty strings
allowed_origins = list(set(filter(None, allowed_origins)))

# Log CORS configuration for debugging
logger.info(f"🔧 CORS allowed origins: {allowed_origins}")
logger.info(f"🌍 FRONTEND_URL from env: {settings.frontend_url}")
logger.info(f"🔒 Environment: {settings.environment}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "QuestPath API", 
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms"""
    return {"status": "healthy", "environment": settings.environment}