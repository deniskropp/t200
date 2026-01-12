from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Core App Settings
    APP_NAME: str = "Orion Collective System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    ARTIFACTS_DIR: Path = BASE_DIR / "artifacts"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///ocs.db"
    
    # Workflow
    MAX_REFINEMENT_LOOPS: int = 3
    AUTO_APPROVE_THRESHOLD: float = 0.95

settings = Settings()
