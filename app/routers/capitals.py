from fastapi import APIRouter, HTTPException, Depends
from app.services.countries import CountryService
from app.core.logging import logger

router = APIRouter()

@router.get("/african-capitals", summary="Get capital cities of African countries grouped by region")
async def get_african_capitals(country_service: CountryService = Depends()):
    """
    Fetches African countries from the REST Countries API and returns their names and capitals,
    grouped and ordered by subregion.
    """
    logger.info("Fetching African capitals")
    try:
        result = await country_service.get_african_capitals_by_region()
        return {"african_capitals_by_region": result}
    except Exception as e:
        logger.error(f"Error fetching African capitals: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch country data. Service may be temporarily unavailable."
        )