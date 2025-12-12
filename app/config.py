"""
Configuration settings for the application
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB Configuration
    MONGODB_URL: str = "mongodb://localhost:27017/"
    DATABASE_NAME: str = "master_database"
    
    # JWT Configuration
    SECRET_KEY: str = "dev-secret-key-change-in-production-abc123xyz"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    # Application settings
    APP_NAME: str = "Organization Management Service"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
