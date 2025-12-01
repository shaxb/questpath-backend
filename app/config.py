from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 60 * 24 * 30
    openai_api_key: str

    model_config = SettingsConfigDict(env_file="app/.env", env_file_encoding="utf-8")

settings = Settings()   