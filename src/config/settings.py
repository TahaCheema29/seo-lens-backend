from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_cloud_api_key_1: str = Field(..., env="GOOGLE_CLOUD_API_KEY_1")
    google_cloud_api_key_2: str = Field(..., env="GOOGLE_CLOUD_API_KEY_2")
    google_cloud_api_key_3: str = Field(..., env="GOOGLE_CLOUD_API_KEY_3")
    redis_url:str=Field(..., env="REDIS_URL")
    redis_password: str = Field(..., env="REDIS_PASSWORD") 
    google_cloud_cse:str=Field(...,env="GOOGLE_CLOUD_CSE")
    pagespeed_api_key: str=Field(...,env="PAGESPEED_API_KEY")

    class Config:
        env_file = ".env.local"

settings = Settings()