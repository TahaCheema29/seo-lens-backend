from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App Settings
    debug: bool = Field(default=False, env="DEBUG")
    app_name: str = Field(default="SEO Lens", env="APP_NAME")
    
    # Google API Keys
    google_cloud_api_key_1: str = Field(default="", env="GOOGLE_CLOUD_API_KEY_1")
    google_cloud_api_key_2: str = Field(default="", env="GOOGLE_CLOUD_API_KEY_2")
    google_cloud_api_key_3: str = Field(default="", env="GOOGLE_CLOUD_API_KEY_3")
    google_cloud_cse: str = Field(default="", env="GOOGLE_CLOUD_CSE")
    pagespeed_api_key: str = Field(default="", env="PAGESPEED_API_KEY")
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/seo_lens",
        env="DATABASE_URL"
    )
    
    # JWT Settings
    jwt_secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=1440, env="JWT_EXPIRATION_MINUTES")

    class Config:
        env_file = ".env.local"
        extra = "ignore"


settings = Settings()