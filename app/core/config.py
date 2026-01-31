from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TrustLayer AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    
    # Security
    OPENAI_API_KEY: str = "sk-mock-key" # Default mock key for hackathon mode
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./trustlayer.db"

    class Config:
        env_file = ".env"

settings = Settings()
