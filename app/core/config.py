import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Information
    APP_TITLE: str = "African Capitals API"
    APP_DESCRIPTION: str = "Returns the capital cities of African countries grouped by region using the REST Countries public API."
    APP_VERSION: str = "1.2.0"
    
    # External API
    REST_COUNTRIES_URL: str = "https://restcountries.com/v3.1/region/africa"
    
    # Cache settings
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "False").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # Default: 1 hour
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Timeout settings
    EXTERNAL_API_TIMEOUT: int = int(os.getenv("EXTERNAL_API_TIMEOUT", "10"))  # seconds
    
    # Region ordering
    REGION_ORDER: list = ["Northern Africa", "Western Africa", "Eastern Africa", "Southern Africa", "Central Africa"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()