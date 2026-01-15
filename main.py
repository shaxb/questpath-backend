from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.logger import logger
from app.logging_config import configure_external_loggers
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


# Initialize Sentry error tracking (only if DSN provided)
if settings.sentry_dsn and settings.sentry_dsn.startswith("https://"):
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        # Send user context with errors
        send_default_pii=False,  # Don't send passwords/tokens
    )
    logger.info("sentry_initialized", 
                environment=settings.environment,
                traces_sample_rate=settings.sentry_traces_sample_rate)
else:
    logger.info("sentry_disabled", 
                message="SENTRY_DSN not configured - errors will only be logged locally")


app = FastAPI(title="QuestPath API", version="1.0.0")

# Configure all external library logging
configure_external_loggers()

# CORS middleware - allows frontend to call API
allowed_origins = [
    "http://localhost:3000",  # Local development
    "http://localhost:3001",
    "http://192.168.100.151:3000",
    settings.frontend_url,
]

# Remove duplicates and empty strings
allowed_origins = list(set(filter(None, allowed_origins)))


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware for request tracking and security
from app.middleware import add_request_tracking, add_security_headers

app.middleware("http")(add_request_tracking)
app.middleware("http")(add_security_headers)

 


# Include your routers here
from app.users import router as users_router
from app.goals import router as goals_router
from app.quizzes import router as quizzes_router
from app.health import router as health_router
from app.progression import router as progression_router
from app.leaderboard import router as leaderboard_router


app.include_router(users_router)
app.include_router(goals_router)
app.include_router(quizzes_router)
app.include_router(progression_router)
app.include_router(leaderboard_router)
app.include_router(health_router)  # Health check endpoints


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "QuestPath API", 
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


