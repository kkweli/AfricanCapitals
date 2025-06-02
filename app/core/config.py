import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Information
    APP_TITLE: str = "African Capitals API with WebGL Map"
    APP_DESCRIPTION: str = "Returns the capital cities of African countries grouped by region with interactive WebGL map and economic data."
    APP_VERSION: str = "1.3.0"
    
    # External API
    REST_COUNTRIES_URL: str = "https://restcountries.com/v3.1/region/africa"
    
    # Cache settings
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "True").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # Default: 1 hour
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Timeout settings
    EXTERNAL_API_TIMEOUT: int = int(os.getenv("EXTERNAL_API_TIMEOUT", "10"))  # seconds
    
    # Region ordering
    REGION_ORDER: list = ["Northern Africa", "Western Africa", "Eastern Africa", "Southern Africa", "Central Africa"]
    
    # World Bank API settings
    WORLD_BANK_API_URL: str = "https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}?format=json&per_page=1&mrnev=1"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()