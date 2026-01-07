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
    
    # OAuth
    google_client_id: str | None = None
    google_client_secret: str | None = None
    
    # OpenAI
    openai_api_key: str
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    # Environment
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()   