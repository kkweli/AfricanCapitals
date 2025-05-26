from fastapi import FastAPI
import httpx
from datetime import datetime
import sys

# Use zoneinfo for local timezone (Python 3.9+)
try:
    from zoneinfo import ZoneInfo
    import os
    # Try to get the system's timezone from environment or default to Etc/UTC
    tz_key = os.environ.get("TZ") or "Etc/UTC"
    try:
        LOCAL_TZ = ZoneInfo(tz_key)
    except Exception:
        # Fallback to system local timezone if ZoneInfo fails
        LOCAL_TZ = None
except ImportError:
    # For Python <3.9 fallback to None
    LOCAL_TZ = None

app = FastAPI(
    title="African Capitals API",
    description="Returns the capital cities of African countries grouped by region using the REST Countries public API.",
    version="1.1.0"
)

# Define the order of regions
REGION_ORDER = ["Northern Africa", "Western Africa", "Eastern Africa", "Southern Africa", "Central Africa"]

REST_COUNTRIES_URL = "https://restcountries.com/v3.1/region/africa"

@app.get("/health", summary="Health check endpoint")
async def health_check():
    """
    Health check endpoint that attempts to fetch data from the REST Countries API.
    Returns the current timestamp (host local timezone) and status.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(REST_COUNTRIES_URL, timeout=5)
            response.raise_for_status()
        # Use ZoneInfo if available, else fallback to system local time
        if LOCAL_TZ:
            now = datetime.now(LOCAL_TZ)
        else:
            now = datetime.now().astimezone()
        return {
            "status": "ok",
            "last_sync": now.isoformat()
        }
    except Exception as e:
        return {
            "status": "exception",
            "last_sync": None,
            "error": str(e)
        }

@app.get("/african-capitals", summary="Get capital cities of African countries grouped by region")
async def get_african_capitals():
    """
    Fetches African countries from the REST Countries API and returns their names and capitals,
    grouped and ordered by subregion.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(REST_COUNTRIES_URL)
        response.raise_for_status()
        countries = response.json()

    # Group countries by subregion
    grouped = {region: [] for region in REGION_ORDER}
    for country in countries:
        name = country.get("name", {}).get("common")
        capitals = country.get("capital", [])
        capital = ", ".join(capitals) if capitals else None
        subregion = country.get("subregion")
        if name and capital and subregion in grouped:
            grouped[subregion].append({"country": name, "capital": capital})

    # Prepare the result in the specified order
    result = []
    for region in REGION_ORDER:
        if grouped[region]:
            result.append({     
                "region": region,
                "countries": sorted(grouped[region], key=lambda x: x["country"])
            })

    return {"african_capitals_by_region": result}

# Run the app with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
