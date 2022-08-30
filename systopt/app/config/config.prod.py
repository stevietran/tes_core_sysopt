from pydantic import BaseSettings

class Settings(BaseSettings):
    WEB_API_URL: str = "http://tes-backend:8001/api/v1"

    class Config:
        case_sensitive = True

# instantiate the Settings class so that app.core.config.settings can beimported throughout the project.
settings = Settings()
