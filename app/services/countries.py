import httpx
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
    
    async def fetch_countries(self):
        """Fetch countries from the REST Countries API"""
        logger.debug(f"Fetching countries from {self.rest_countries_url}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.rest_countries_url, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                logger.error("Timeout while fetching countries")
                raise Exception("External API request timed out")
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error while fetching countries: {e}")
                raise Exception(f"External API returned error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Unexpected error while fetching countries: {str(e)}")
                raise
    
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