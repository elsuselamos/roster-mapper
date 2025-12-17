"""
Configuration Module
====================
Pydantic settings for application configuration.
Reads from environment variables and .env file.

Supports both local development and Google Cloud Run deployment.

Author: datnguyentien@vietjetair.com
"""

import os
from typing import List
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.
    
    All settings can be overridden via environment variables.
    Environment variables take precedence over .env file values.
    
    Cloud Run Deployment:
    - Set STORAGE_TYPE=local
    - STORAGE_DIR=/tmp/uploads
    - OUTPUT_DIR=/tmp/output
    - PORT will be set by Cloud Run automatically
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "Vietjet Roster Mapper"
    APP_VERSION: str = "1.3.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Server - PORT defaults to 8080 for Cloud Run compatibility
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/roster_mapper"
    DB_ECHO: bool = False
    
    # Storage configuration
    STORAGE_TYPE: str = "local"  # "local" for ephemeral, future: "gcs"
    MAPPING_DIR: Path = Path("./mappings")
    STORAGE_DIR: Path = Path(os.getenv("STORAGE_DIR", "./uploads"))
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "./uploads/processed"))
    TEMP_DIR: Path = Path(os.getenv("TEMP_DIR", "./temp"))
    
    # Cloud Run specific
    IS_CLOUD_RUN: bool = os.getenv("K_SERVICE", "") != ""  # K_SERVICE is set by Cloud Run
    
    # Features
    AUTO_DETECT_STATION: bool = True
    
    # Security
    SECRET_KEY: str = "change-me-in-production"
    API_KEY: str = "your-api-key-here"
    
    # ComPDF API
    # Note: Get these from ComPDF API console: https://api.compdf.com -> API Key section
    COMPDF_PUBLIC_KEY: str = os.getenv("COMPDF_PUBLIC_KEY", "public_key_7eedffb6441e996592f3f612f6e22aea")
    COMPDF_SECRET_KEY: str = os.getenv("COMPDF_SECRET_KEY", "")
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    @field_validator("MAPPING_DIR", "STORAGE_DIR", "OUTPUT_DIR", "TEMP_DIR", mode="before")
    @classmethod
    def ensure_path(cls, v: str | Path) -> Path:
        """Convert string paths to Path objects."""
        return Path(v) if isinstance(v, str) else v
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.APP_ENV.lower() == "development"
    
    def get_station_mapping_path(self, station: str) -> Path:
        """
        Get the mapping file path for a specific station.
        
        Args:
            station: Station code (e.g., 'SGN', 'HAN')
            
        Returns:
            Path to the station's latest mapping file.
        """
        return self.MAPPING_DIR / station / "latest.json"
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [self.MAPPING_DIR, self.STORAGE_DIR, self.OUTPUT_DIR, self.TEMP_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
        # Also ensure results subdirectory exists
        (self.OUTPUT_DIR / "results").mkdir(parents=True, exist_ok=True)
    
    @property
    def is_cloud_run(self) -> bool:
        """Check if running on Google Cloud Run."""
        return self.IS_CLOUD_RUN or os.getenv("K_SERVICE", "") != ""


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()

