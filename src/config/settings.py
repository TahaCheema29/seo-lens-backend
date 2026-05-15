import logging
import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.docker",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # App Settings
    debug: bool = Field(default=False, validation_alias="DEBUG")
    app_name: str = Field(default="SEO Lens", validation_alias="APP_NAME")
    
    # Google API Keys
    google_cloud_api_key_1: str = Field(default="", validation_alias="GOOGLE_CLOUD_API_KEY_1")
    google_cloud_api_key_2: str = Field(default="", validation_alias="GOOGLE_CLOUD_API_KEY_2")
    google_cloud_api_key_3: str = Field(default="", validation_alias="GOOGLE_CLOUD_API_KEY_3")
    google_cloud_cse: str = Field(default="", validation_alias="GOOGLE_CLOUD_CSE")
    pagespeed_api_key: str = Field(default="", validation_alias="PAGESPEED_API_KEY")
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379",
        validation_alias="REDIS_URL"
    )
    redis_password: str = Field(default="", validation_alias="REDIS_PASSWORD")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/seo_lens",
        validation_alias="DATABASE_URL"
    )
    
    # JWT Settings
    jwt_secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        validation_alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=1440, validation_alias="JWT_EXPIRATION_MINUTES")
    
    # Email Settings
    email_provider: str = Field(default="console", validation_alias="EMAIL_PROVIDER")
    sendgrid_api_key: str = Field(default="", validation_alias="SENDGRID_API_KEY")
    sendgrid_from_email: str = Field(default="noreply@seo-lens.com", validation_alias="SENDGRID_FROM_EMAIL")
    sendgrid_from_name: str = Field(default="SEO Lens", validation_alias="SENDGRID_FROM_NAME")
    
    # Stripe Settings
    stripe_secret_key: str = Field(default="", validation_alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(default="", validation_alias="STRIPE_SECRET_WEBHOOK_KEY")
    stripe_price_id: str = Field(default="price_1TXCz9RsBYmDUkzAUAMSKxbR", validation_alias="STRIPE_PRICE_ID")
    frontend_url: str = Field(default="http://localhost:3000", validation_alias="FRONTEND_URL")


settings = Settings()