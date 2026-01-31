from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TrustLayer AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    
    # Security
    OPENAI_API_KEY: str = "sk-mock-key" # Default mock key for hackathon mode
    
    # Database
    # Use absolute path to ensure Proxy and Streamlit share the SAME file
    import os
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/trustlayer.db"

    class Config:
        env_file = ".env"

settings = Settings()
