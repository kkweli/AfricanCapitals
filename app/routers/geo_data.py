from fastapi import APIRouter, HTTPException, Depends, Path
from app.services.geo_data import GeoDataService
from app.core.logging import logger

router = APIRouter()

@router.get("/map-data", summary="Get GeoJSON data for African countries")
async def get_map_data(geo_service: GeoDataService = Depends()):
    """
    Fetches GeoJSON data for all African countries for map rendering.
    """
    logger.info("Fetching map data for African countries")
    try:
        result = await geo_service.get_all_countries_geojson()
        return result
    except Exception as e:
        logger.error(f"Error fetching map data: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch map data. Service may be temporarily unavailable."
        )

@router.get("/map-data/{country_code}", summary="Get GeoJSON data for a specific African country")
async def get_country_map_data(
    country_code: str = Path(..., description="ISO 3166-1 alpha-2 or alpha-3 country code"),
    geo_service: GeoDataService = Depends()
):
    """
    Fetches GeoJSON data for a specific African country for map rendering.
    """
    logger.info(f"Fetching map data for country: {country_code}")
    try:
        result = await geo_service.get_country_geojson(country_code)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Map data not found for country code: {country_code}"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching map data for {country_code}: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch map data. Service may be temporarily unavailable."
        )