from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Redis (Upstash)
    redis_url: str = "redis://localhost:6379"
    
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # 15 minutes
    refresh_token_expire_minutes: int = 60 * 24 * 30  # 30 days
    
    # OpenAI
    openai_api_key: str
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    # Environment
    environment: str = "development"
    
    # Logging control
    debug: bool = True  # Set to False in production
    log_sql_queries: bool = False  # SQLAlchemy query logging
    log_http_requests: bool = True  # Uvicorn access logs
    
    # Error Tracking
    sentry_dsn: str | None = None  # Add to .env for production error tracking
    sentry_traces_sample_rate: float = 0.1  # 10% of requests traced

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()   