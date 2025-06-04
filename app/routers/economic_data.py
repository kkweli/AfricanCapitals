from fastapi import APIRouter, HTTPException, Depends, Path, Query
from app.services.economic_data import EconomicDataService
from app.core.logging import logger
from typing import Optional

router = APIRouter()

@router.get("/economic-data", summary="Get economic data for African countries")
async def get_economic_data(
    economic_service: EconomicDataService = Depends()
):
    """
    Fetches economic data for African countries including GDP, population, and key sectors.
    """
    logger.info("Fetching economic data for African countries")
    try:
        result = await economic_service.get_all_economic_data()
        return {"economic_data": result}
    except Exception as e:
        logger.error(f"Error fetching economic data: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch economic data. Service may be temporarily unavailable."
        )

@router.get("/economic-data/{country_code}",
    summary="Get economic data for a specific African country",
    responses={
        200: {
            "description": "Successfully retrieved economic data",
            "content": {
                "application/json": {
                    "example": {
                        "country": {
                            "name": "Kenya",
                            "code": "KE",
                            "capital": "Nairobi",
                            "region": "Eastern Africa"
                        },
                        "economy": {
                            "gdp": 98.84,
                            "gdp_growth": 5.6,
                            "currency": "Kenyan Shilling",
                            "key_sectors": [
                                {
                                    "name": "Agriculture",
                                    "value": 34.2,
                                    "contribution": 35
                                }
                            ]
                        }
                    }
                }
            }
        }
    }
)
async def get_country_economic_data(
    country_code: str = Path(..., description="ISO 3166-1 alpha-2 or alpha-3 country code"),
    economic_service: EconomicDataService = Depends()
):
    """
    Fetches economic data for a specific African country including GDP, population, and key sectors.
    """
    logger.info(f"Fetching economic data for country: {country_code}")
    try:
        result = await economic_service.get_country_economic_data(country_code)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Economic data not found for country code: {country_code}"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching economic data for {country_code}: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch economic data. Service may be temporarily unavailable."
        )

@router.get("/country-profile/{country_code}", summary="Get comprehensive profile for a specific African country")
async def get_country_profile(
    country_code: str = Path(..., description="ISO 3166-1 alpha-2 or alpha-3 country code"),
    economic_service: EconomicDataService = Depends()
):
    """
    Fetches a comprehensive profile for a specific African country including:
    - Basic information (name, capital, etc.)
    - Geographic data (boundaries, coordinates)
    - Economic data (GDP, key sectors)
    - Demographic data (population, growth rate)
    """
    logger.info(f"Fetching country profile for: {country_code}")
    try:
        result = await economic_service.get_country_profile(country_code)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Country profile not found for country code: {country_code}"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching country profile for {country_code}: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch country profile. Service may be temporarily unavailable."
        )