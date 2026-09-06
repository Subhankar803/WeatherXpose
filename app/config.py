"""
Central configuration loader.
Reads all values from environment variables (via .env file).
NOTHING else in the codebase should call os.environ directly —
always import `settings` from here so config stays in one place.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # External APIs
    imd_api_base_url: str = "https://api.imd.gov.in"
    imd_api_key: str = ""
    windy_api_key: str = ""
    gnews_api_key: str = ""
    newsdata_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "weather-platform-bot"
    telegram_bot_token: str = ""

    # Object storage
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "weather-media"

    # App
    environment: str = "development"
    debug: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
