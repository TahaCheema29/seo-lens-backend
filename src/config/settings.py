from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_cloud_api_key_1: str = Field(..., env="GOOGLE_CLOUD_API_KEY_1")
    google_cloud_api_key_2: str = Field(..., env="GOOGLE_CLOUD_API_KEY_2")
    google_cloud_api_key_3: str = Field(..., env="GOOGLE_CLOUD_API_KEY_3")
    redis_url:str=Field(..., env="REDIS_URL")
    redis_password: str = Field(..., env="REDIS_PASSWORD") 
    google_cloud_cse:str=Field(...,env="GOOGLE_CLOUD_CSE")
    database_url: str = Field(..., env="DATABASE_URL")

    # Auth (JWT)
    jwt_secret_key: str = Field("dev-change-me", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(60, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    class Config:
        env_file = ".env.local"

settings = Settings()