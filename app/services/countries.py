import httpx
import asyncio
import time
from fastapi import Depends
from app.core.config import settings
from app.core.logging import logger

class CountryService:
    """
    Service for fetching and processing country data
    """
    
    def __init__(self):
        self.rest_countries_url = settings.REST_COUNTRIES_URL
        self.region_order = settings.REGION_ORDER
        self.timeout = settings.EXTERNAL_API_TIMEOUT
        self._countries_cache = None
        self._countries_cache_time = 0
        self._countries_cache_ttl = settings.CACHE_TTL
        self._countries_cache_lock = asyncio.Lock()

    async def fetch_countries(self):
        """Fetch countries from the REST Countries API"""
        now = time.time()
        async with self._countries_cache_lock:
            if (
                settings.CACHE_ENABLED and
                self._countries_cache and
                now - self._countries_cache_time < self._countries_cache_ttl
            ):
                return self._countries_cache
            # Fetch from RestCountries API
            async with httpx.AsyncClient(timeout=settings.EXTERNAL_API_TIMEOUT) as client:
                response = await client.get(settings.REST_COUNTRIES_URL)
                response.raise_for_status()
                countries = response.json()
                self._countries_cache = countries
                self._countries_cache_time = now
                return countries
    
    async def get_african_capitals_by_region(self):
        """
        Fetches African countries and returns their capitals grouped by region
        """
        countries = await self.fetch_countries()
        
        grouped = {region: [] for region in self.region_order}
        for country in countries:
            name = country.get("name", {}).get("common")
            capitals = country.get("capital", [])
            capital = ", ".join(capitals) if capitals else None
            subregion = country.get("subregion")
            if name and capital and subregion in grouped:
                grouped[subregion].append({"country": name, "capital": capital})

        result = []
        for region in self.region_order:
            if grouped[region]:
                result.append({     
                    "region": region,
                    "countries": sorted(grouped[region], key=lambda x: x["country"])
                })
                
        return result
    
    async def get_country_data(self, country_code):
        """
        Fetch a single country's data by ISO 3166-1 alpha-2 or alpha-3 code.
        """
        countries = await self.fetch_countries()
        country_code = country_code.upper()
        return next(
            (
                c for c in countries
                if c.get("cca2", "").upper() == country_code or c.get("cca3", "").upper() == country_code
            ),
            None
        )