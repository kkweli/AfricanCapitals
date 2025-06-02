import httpx
import json
import os
from fastapi import Depends
from app.core.config import settings
from app.core.logging import logger

class GeoDataService:
    """
    Service for fetching and processing geographic data for African countries
    """
    
    def __init__(self):
        self.timeout = settings.EXTERNAL_API_TIMEOUT
        self.natural_earth_url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
    
    async def fetch_geojson(self):
        """Fetch GeoJSON data from Natural Earth"""
        cache_file = os.path.join(self.cache_dir, "countries.geojson")
        
        # Check if we have cached data
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading cached GeoJSON: {str(e)}")
                # If there's an error reading the cache, fetch from source
        
        # Fetch from source
        logger.debug(f"Fetching GeoJSON from {self.natural_earth_url}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.natural_earth_url, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                
                # Cache the data
                try:
                    with open(cache_file, 'w') as f:
                        json.dump(data, f)
                except Exception as e:
                    logger.error(f"Error caching GeoJSON: {str(e)}")
                
                return data
            except Exception as e:
                logger.error(f"Error fetching GeoJSON: {str(e)}")
                
                # If we have a fallback file, use it
                fallback_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "countries.geojson")
                if os.path.exists(fallback_file):
                    try:
                        with open(fallback_file, 'r') as f:
                            return json.load(f)
                    except Exception as fallback_error:
                        logger.error(f"Error reading fallback GeoJSON: {str(fallback_error)}")
                
                # If all else fails, return a minimal valid GeoJSON
                return {
                    "type": "FeatureCollection",
                    "features": []
                }
    
    async def get_all_countries_geojson(self):
        """
        Fetches GeoJSON data for all African countries
        """
        all_geojson = await self.fetch_geojson()
        
        # Filter for African countries
        african_features = [
            feature for feature in all_geojson.get("features", [])
            if feature.get("properties", {}).get("CONTINENT") == "Africa"
        ]
        
        return {
            "type": "FeatureCollection",
            "features": african_features
        }
    
    async def get_country_geojson(self, country_code):
        """
        Fetches GeoJSON data for a specific country
        """
        all_geojson = await self.fetch_geojson()
        
        # Normalize country code
        country_code = country_code.upper()
        
        # Find the country feature
        country_feature = next(
            (feature for feature in all_geojson.get("features", [])
             if feature.get("properties", {}).get("ISO_A2") == country_code or
                feature.get("properties", {}).get("ISO_A3") == country_code),
            None
        )
        
        if not country_feature:
            return None
            
        return {
            "type": "FeatureCollection",
            "features": [country_feature]
        }