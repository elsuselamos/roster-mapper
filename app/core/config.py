"""
Configuration Module
====================
Pydantic settings for application configuration.
Reads from environment variables and .env file.

Author: datnguyentien@vietjetair.com
"""

from typing import List
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.
    
    All settings can be overridden via environment variables.
    Environment variables take precedence over .env file values.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "roster-mapper"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/roster_mapper"
    DB_ECHO: bool = False
    
    # Storage paths
    MAPPING_DIR: Path = Path("./mappings")
    STORAGE_DIR: Path = Path("./uploads")
    TEMP_DIR: Path = Path("./temp")
    
    # Features
    AUTO_DETECT_STATION: bool = True
    
    # Security
    SECRET_KEY: str = "change-me-in-production"
    API_KEY: str = "your-api-key-here"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    @field_validator("MAPPING_DIR", "STORAGE_DIR", "TEMP_DIR", mode="before")
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
        for directory in [self.MAPPING_DIR, self.STORAGE_DIR, self.TEMP_DIR]:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()

