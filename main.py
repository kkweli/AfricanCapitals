from fastapi import FastAPI
from datetime import datetime
import sys
import uvicorn
import httpx

# Use zoneinfo for local timezone (Python 3.9+)
try:
    from zoneinfo import ZoneInfo
    import os
    tz_key = os.environ.get("TZ") or "Etc/UTC"
    try:
        LOCAL_TZ = ZoneInfo(tz_key)
    except Exception:
        LOCAL_TZ = None
except ImportError:
    LOCAL_TZ = None

app = FastAPI(
    title="African Capitals API",
    description="Returns the capital cities of African countries grouped by region using the REST Countries public API.",
    version="1.1.0"
)

REGION_ORDER = ["Northern Africa", "Western Africa", "Eastern Africa", "Southern Africa", "Central Africa"]

REST_COUNTRIES_URL = "https://restcountries.com/v3.1/region/africa"

@app.get("/health", summary="Health check endpoint")
def health_check():
    """
    Simple health check endpoint.
    Returns OK status and the current timestamp (host local timezone).
    """
    if LOCAL_TZ:
        now = datetime.now(LOCAL_TZ)
    else:
        now = datetime.now().astimezone()
    return {
        "status": "ok",
        "time": now.isoformat()
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

    grouped = {region: [] for region in REGION_ORDER}
    for country in countries:
        name = country.get("name", {}).get("common")
        capitals = country.get("capital", [])
        capital = ", ".join(capitals) if capitals else None
        subregion = country.get("subregion")
        if name and capital and subregion in grouped:
            grouped[subregion].append({"country": name, "capital": capital})

    result = []
    for region in REGION_ORDER:
        if grouped[region]:
            result.append({     
                "region": region,
                "countries": sorted(grouped[region], key=lambda x: x["country"])
            })

    return {"african_capitals_by_region": result}

if __name__ == "__main__":    
    uvicorn.run(app, host="0.0.0.0", port=8000)