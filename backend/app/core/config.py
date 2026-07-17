import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Media Detection Platform"
    API_V1_STR: str = "/api/v1"
    
    # Path settings
    UPLOAD_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../uploads"))
    REPORT_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../reports"))

    class Config:
        case_sensitive = True

settings = Settings()

# Automate folder creation
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORT_DIR, exist_ok=True)