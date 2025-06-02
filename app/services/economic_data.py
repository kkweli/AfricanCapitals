import httpx
from fastapi import Depends
from app.core.config import settings
from app.core.logging import logger
from app.services.countries import CountryService
from app.services.geo_data import GeoDataService

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
        
        # Hardcoded key sectors data for prototype
        # In production, this would come from a database or another API
        self.key_sectors = {
            "KE": [  # Kenya
                {"name": "Agriculture", "contribution": 34.5, "value": 33.9},
                {"name": "Tourism", "contribution": 8.8, "value": 8.7},
                {"name": "Manufacturing", "contribution": 7.7, "value": 7.6}
            ],
            "NG": [  # Nigeria
                {"name": "Oil & Gas", "contribution": 8.6, "value": 38.7},
                {"name": "Agriculture", "contribution": 26.2, "value": 117.9},
                {"name": "Telecommunications", "contribution": 11.2, "value": 50.4}
            ],
            "ZA": [  # South Africa
                {"name": "Mining", "contribution": 8.2, "value": 29.9},
                {"name": "Finance", "contribution": 20.3, "value": 74.1},
                {"name": "Manufacturing", "contribution": 13.5, "value": 49.3}
            ],
            # Default sectors for other countries
            "default": [
                {"name": "Agriculture", "contribution": 25.0, "value": 15.0},
                {"name": "Services", "contribution": 45.0, "value": 27.0},
                {"name": "Industry", "contribution": 30.0, "value": 18.0}
            ]
        }
    
    async def fetch_world_bank_data(self, country_code, indicator):
        """Fetch data from World Bank API"""
        url = self.world_bank_api_url.format(country_code=country_code, indicator=indicator)
        logger.debug(f"Fetching World Bank data from {url}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                
                # World Bank API returns a list with metadata as first element and data as second
                if len(data) > 1 and data[1] and len(data[1]) > 0:
                    return data[1][0]["value"]
                return None
            except Exception as e:
                logger.error(f"Error fetching World Bank data: {str(e)}")
                return None
    
    async def get_country_economic_data(self, country_code):
        """
        Fetches economic data for a specific country
        """
        # For prototype, we'll use a mix of real API calls and mock data
        # In production, all data would come from reliable APIs or databases
        
        # Normalize country code to ISO 3166-1 alpha-2
        country_code = country_code.upper()
        if len(country_code) == 3:
            # Convert alpha-3 to alpha-2 (simplified for prototype)
            # In production, use a proper country code conversion library
            code_mapping = {"KEN": "KE", "NGA": "NG", "ZAF": "ZA", "EGY": "EG", "GHA": "GH"}
            country_code = code_mapping.get(country_code, country_code[:2])
        
        # Fetch basic country data
        countries = await self.country_service.fetch_countries()
        country_data = next((c for c in countries if c.get("cca2") == country_code or c.get("cca3") == country_code), None)
        
        if not country_data:
            return None
        
        # Fetch economic indicators
        gdp = await self.fetch_world_bank_data(country_code, self.indicators["gdp"])
        gdp_growth = await self.fetch_world_bank_data(country_code, self.indicators["gdp_growth"])
        population = await self.fetch_world_bank_data(country_code, self.indicators["population"])
        population_growth = await self.fetch_world_bank_data(country_code, self.indicators["population_growth"])
        
        # Get key sectors (mock data for prototype)
        sectors = self.key_sectors.get(country_code, self.key_sectors["default"])
        
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
                "median_age": country_data.get("median_age", 25)  # Default if not available
            }
        }
    
    async def get_all_economic_data(self):
        """
        Fetches economic data for all African countries
        """
        countries = await self.country_service.fetch_countries()
        result = []
        
        for country in countries:
            country_code = country.get("cca2")
            if not country_code:
                continue
                
            # For prototype, we'll just get basic data to avoid too many API calls
            result.append({
                "name": country.get("name", {}).get("common"),
                "code": country_code,
                "capital": ", ".join(country.get("capital", [])) if country.get("capital") else None,
                "population": await self.fetch_world_bank_data(country_code, self.indicators["population"]),
                "gdp": await self.fetch_world_bank_data(country_code, self.indicators["gdp"])
            })
            
        return result
    
    async def get_country_profile(self, country_code):
        """
        Fetches a comprehensive profile for a specific country
        """
        # Get economic data
        economic_data = await self.get_country_economic_data(country_code)
        if not economic_data:
            return None
            
        # Get geographic data
        geo_data = await self.geo_service.get_country_geojson(country_code)
        
        # Combine data for complete profile
        return {
            **economic_data,
            "geography": {
                "boundaries": geo_data.get("features", [{}])[0].get("geometry") if geo_data else {},
                "capital_coordinates": economic_data.get("country", {}).get("capital_coordinates", [0, 0])
            }
        }