import httpx
import asyncio
import time
from fastapi import Depends
from app.core.config import settings
from app.core.logging import logger
from app.services.countries import CountryService
from app.services.geo_data import GeoDataService
from app.utils.async_utils import gather_with_concurrency

class EconomicDataService:
    """
    Service for fetching and processing economic data for African countries
    """

    def __init__(
        self, 
        country_service: CountryService = Depends(),
        geo_service: GeoDataService = Depends()
    ):
        self.country_service = country_service
        self.geo_service = geo_service
        self.world_bank_api_url = "https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}?format=json&per_page=1&mrnev=1"
        self.timeout = settings.EXTERNAL_API_TIMEOUT

        # World Bank indicators
        self.indicators = {
            "gdp": "NY.GDP.MKTP.CD",  # GDP (current US$)
            "gdp_growth": "NY.GDP.MKTP.KD.ZG",  # GDP growth (annual %)
            "population": "SP.POP.TOTL",  # Population, total
            "population_growth": "SP.POP.GROW",  # Population growth (annual %)
        }
        # Sector indicators (percent of GDP)
        self.sector_indicators = {
            "Agriculture": "NV.AGR.TOTL.ZS",
            "Industry": "NV.IND.TOTL.ZS",
            "Services": "NV.SRV.TOTL.ZS"
        }

        self._wb_cache = {}
        self._wb_cache_lock = asyncio.Lock()
        self._wb_cache_ttl = settings.CACHE_TTL

    async def fetch_world_bank_data(self, country_code, indicator):
        cache_key = f"{country_code}:{indicator}"
        now = time.time()
        async with self._wb_cache_lock:
            cached = self._wb_cache.get(cache_key)
            if (
                settings.CACHE_ENABLED and
                cached and
                now - cached['timestamp'] < self._wb_cache_ttl
            ):
                return cached['value']

        url = self.world_bank_api_url.format(
            country_code=country_code, 
            indicator=indicator
        )
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                value = None
                if len(data) > 1 and data[1] and len(data[1]) > 0:
                    value = data[1][0].get("value")
                async with self._wb_cache_lock:
                    self._wb_cache[cache_key] = {'value': value, 'timestamp': now}
                return value
            except Exception as e:
                logger.error(f"Error fetching World Bank data: {str(e)}")
                return None

    async def fetch_sector_data(self, country_code, gdp):
        # Fetch sector % of GDP from World Bank
        results = await asyncio.gather(
            *[self.fetch_world_bank_data(country_code, ind) for ind in self.sector_indicators.values()]
        )
        sectors = []
        for name, percent in zip(self.sector_indicators.keys(), results):
            if percent is not None:
                value = round(gdp * percent / 100 / 1e9, 2) if gdp and percent else None  # in billions
                sectors.append({
                    "name": name,
                    "contribution": percent,  # % of GDP
                    "value": value
                })
        return sectors

    async def get_country_economic_data(self, country_code):
        """
        Fetches economic data for a specific country
        """
        country_code = country_code.upper()
        if len(country_code) == 3:
            code_mapping = {"KEN": "KE", "NGA": "NG", "ZAF": "ZA", "EGY": "EG", "GHA": "GH"}
            country_code = code_mapping.get(country_code, country_code[:2])

        countries = await self.country_service.fetch_countries()
        country_data = next((c for c in countries if c.get("cca2") == country_code or c.get("cca3") == country_code), None)
        if not country_data:
            return None

        gdp = await self.fetch_world_bank_data(country_code, self.indicators["gdp"])
        try:
            gdp_growth = await self.fetch_world_bank_data(country_code, self.indicators["gdp_growth"])
        except Exception:
            gdp_growth = None
        population = await self.fetch_world_bank_data(country_code, self.indicators["population"])
        try:
            population_growth = await self.fetch_world_bank_data(country_code, self.indicators["population_growth"])
        except Exception:
            population_growth = None
        sectors = await self.fetch_sector_data(country_code, gdp)

        # Return whatever data is available
        return {
            "country": {
                "name": country_data.get("name", {}).get("common"),
                "code": country_code,
                "capital": ", ".join(country_data.get("capital", [])) if country_data.get("capital") else None,
                "region": country_data.get("subregion")
            },
            "economy": {
                "gdp": gdp,
                "gdp_growth": gdp_growth,
                "currency": list(country_data.get("currencies", {}).keys())[0] if country_data.get("currencies") else None,
                "key_sectors": sectors
            },
            "demographics": {
                "population": population,
                "growth_rate": population_growth,
                "median_age": country_data.get("median_age", 25)
            }
        }

    async def get_all_economic_data(self):
        countries = await self.country_service.fetch_countries()
        result = []
        for country in countries:
            country_code = country.get("cca2")
            if not country_code:
                continue
            result.append({
                "name": country.get("name", {}).get("common"),
                "code": country_code,
                "capital": ", ".join(country.get("capital", [])) if country.get("capital") else None,
                "population": await self.fetch_world_bank_data(country_code, self.indicators["population"]),
                "gdp": await self.fetch_world_bank_data(country_code, self.indicators["gdp"])
            })
        return result

    async def get_country_profile(self, country_code):
        try:
            indicators = [
                self.fetch_world_bank_data(country_code, ind)
                for ind in self.indicators.values()
            ]
            results = await gather_with_concurrency(
                3,  # Max 3 concurrent requests
                5,  # 5 second timeout
                *indicators
            )
            gdp, gdp_growth, population, population_growth = results
            country_data = await self.country_service.get_country_data(country_code)
            if not country_data:
                return None
            sectors = await self.fetch_sector_data(country_code, gdp)
            return {
                "country": {
                    "name": country_data.get("name", {}).get("common"),
                    "code": country_code,
                    "capital": country_data.get("capital", [""])[0],
                    "region": country_data.get("subregion")
                },
                "economy": {
                    "gdp": gdp,
                    "gdp_growth": gdp_growth,
                    "currency": next(iter(country_data.get("currencies", {}).keys()), None),
                    "key_sectors": sectors
                },
                "demographics": {
                    "population": population,
                    "growth_rate": population_growth,
                    "median_age": country_data.get("median_age", 25)
                }
            }
        except Exception as e:
            logger.error(f"Error getting country profile: {str(e)}")
            return None