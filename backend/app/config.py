from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    """Production-ready configuration for Aviothic AI Platform.
    
    All settings can be overridden via environment variables.
    Medical audit compliant configuration management.
    """
    
    # Database Configuration
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "aviothic_db"
    
    # Model Configuration
    MODEL_PATH: str = str(Path(__file__).parent / "models" / "ensemble.pt")
    DENSITY_MODEL_PATH: str = str(Path(__file__).parent / "models" / "density.pt")
    LESION_MODEL_PATH: str = str(Path(__file__).parent / "models" / "lesion.pt")
    YOLO_MODEL_PATH: str = str(Path(__file__).parent / "models" / "yolov8.pt")
    CALC_PATCH_MODEL_PATH: str = str(Path(__file__).parent / "models" / "calc_patch.pt")
    MODEL_VERSION: str = "v2.0.0-AIMS"
    
    # Storage Configuration
    STATIC_DIR: str = str(Path(__file__).parent / "static")
    UPLOAD_DIR: str = str(Path(__file__).parent / "static" / "uploads")
    GRADCAM_DIR: str = str(Path(__file__).parent / "static" / "gradcam")
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Security Configuration
    SECRET_KEY: str = "your_production_secret_key_here_change_this"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Device Configuration
    DEVICE: str = "cpu"  # or "cuda" for GPU support
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance - loaded once at startup
settings = Settings()