import os
import time
from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any
from app.services.dependencies import get_timezone
from app.core.logging import logger
from http import HTTPStatus
from aiohttp import ClientSession, ClientTimeout, ClientError, TCPConnector
import asyncio
import traceback

router = APIRouter()

# Enhanced monitored endpoints with expected status codes and sample values
MONITORED_ENDPOINTS = [
    {"path": "/api/v1/african-capitals", "name": "African Capitals", "expected_status": 200},
    # Economic data endpoints
    {"path": "/api/v1/economic-data/KE?healthcheck=true", "name": "Economic Data (Kenya)", "expected_status": 200},
    {"path": "/api/v1/economic-data/NG?healthcheck=true", "name": "Economic Data (Nigeria)", "expected_status": 200},
    {"path": "/api/v1/economic-data/ZA?healthcheck=true", "name": "Economic Data (South Africa)", "expected_status": 200},
    {"path": "/api/v1/economic-data/EG?healthcheck=true", "name": "Economic Data (Egypt)", "expected_status": 200},
    # Map data endpoints
    {"path": "/api/v1/map-data/KE", "name": "Map Data (Kenya)", "expected_status": 200},
    {"path": "/api/v1/map-data/NG", "name": "Map Data (Nigeria)", "expected_status": 200},
    {"path": "/api/v1/map-data/ZA", "name": "Map Data (South Africa)", "expected_status": 200},
    # Country profile endpoints
    {"path": "/api/v1/country-profile/KE?healthcheck=true", "name": "Country Profile (Kenya)", "expected_status": 200},
    {"path": "/api/v1/country-profile/NG?healthcheck=true", "name": "Country Profile (Nigeria)", "expected_status": 200},
    {"path": "/api/v1/country-profile/ZA?healthcheck=true", "name": "Country Profile (South Africa)", "expected_status": 200},
    {"path": "/api/v1/country-profile/EG?healthcheck=true", "name": "Country Profile (Egypt)", "expected_status": 200},
    # Frontend
    {"path": "/", "name": "WebGL Map Interface", "expected_status": 200}
]

# Update constants for better connection handling
TIMEOUT_SECONDS = 45 
BATCH_SIZE = 2
MAX_RETRIES = 2
BASE_DELAY = 0.5
MAX_CONCURRENT = 5

# Update base URL to avoid double /api/v1 prefix
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def get_timeout_for_endpoint(path):
    if path.startswith("/api/v1/economic-data"):
        return 60  # seconds
    return 30

async def check_endpoint(session, path: str, name: str, expected_status: int) -> Dict[str, Any]:
    """Check health of a single endpoint with improved timeout handling."""
    start_time = time.time()
    try:
        url = f"{BASE_URL}{path}"
        async with session.get(
            url,
            allow_redirects=True,
            timeout=ClientTimeout(total=get_timeout_for_endpoint(path)),
            headers={"Connection": "close"}
        ) as response:
            elapsed = int((time.time() - start_time) * 1000)
            status_code = response.status
            return {
                "name": name,
                "status": "ok" if status_code == expected_status else "error",
                "http_status": status_code,
                "status_description": HTTPStatus(status_code).phrase if status_code > 0 else "Connection Failed",
                "timestamp": datetime.utcnow().isoformat(),
                "response_time": elapsed,
                "expected_status": expected_status
            }
    except asyncio.TimeoutError as e:
        logger.error(f"Timeout checking endpoint {name}: {str(e)}\n{traceback.format_exc()}")
        return {
            "name": name,
            "status": "timeout",
            "http_status": 0,
            "status_description": "Timeout",
            "timestamp": datetime.utcnow().isoformat(),
            "response_time": int((time.time() - start_time) * 1000),
            "expected_status": expected_status
        }
    except Exception as e:
        logger.error(f"Error checking endpoint {name}: {str(e)}\n{traceback.format_exc()}")
        return {
            "name": name,
            "status": "error",
            "http_status": 0,
            "status_description": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "response_time": int((time.time() - start_time) * 1000),
            "expected_status": expected_status
        }

async def process_endpoints(session, endpoints: list) -> list:
    """Process endpoints with semaphore to limit concurrent connections."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    results = []

    async def check_with_semaphore(endpoint):
        async with semaphore:
            for attempt in range(MAX_RETRIES):
                result = await check_endpoint(
                    session,
                    endpoint["path"],
                    endpoint["name"],
                    endpoint["expected_status"]
                )
                if result["status"] == "ok":
                    return result
                await asyncio.sleep(BASE_DELAY * (2 ** attempt))
            return result

    tasks = [check_with_semaphore(endpoint) for endpoint in endpoints]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [
        result if not isinstance(result, Exception) else {
            "name": endpoints[i]["name"],
            "status": "error",
            "http_status": 0,
            "status_description": str(result),
            "timestamp": datetime.utcnow().isoformat(),
            "response_time": 0,
            "expected_status": endpoints[i]["expected_status"]
        }
        for i, result in enumerate(results)
    ]

@router.get(
    "/health",
    summary="Enhanced health check endpoint with detailed status codes",
    responses={
        200: {
            "description": "Detailed API health status with HTTP codes",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "timestamp": "2024-01-01T12:00:00+00:00",
                        "endpoints": {
                            "Map Data": {
                                "status": "ok",
                                "http_status": 200,
                                "status_description": "OK",
                                "timestamp": "2024-01-01T12:00:00+00:00",
                                "response_time": 42,
                                "expected_status": 200
                            }
                        },
                        "version": "1.0.0",
                        "total_endpoints": 3,
                        "healthy_endpoints": 3,
                        "degraded_endpoints": 0
                    }
                }
            }
        }
    }
)
async def health_check(tz=Depends(get_timezone)) -> Dict[str, Any]:
    """
    Enhanced health check with connection limiting and endpoint status details.
    """
    logger.info("Health check requested")
    now = datetime.now(tz)
    
    health_data = {
        "status": "ok",
        "timestamp": now.isoformat(),
        "endpoints": {},
        "version": "1.0.0",
        "total_endpoints": len(MONITORED_ENDPOINTS),
        "healthy_endpoints": 0,
        "degraded_endpoints": 0
    }
    
    connector = TCPConnector(
        limit=MAX_CONCURRENT,
        limit_per_host=2,
        force_close=True
    )
    timeout = ClientTimeout(total=TIMEOUT_SECONDS * 2)
    
    async with ClientSession(
        connector=connector,
        timeout=timeout,
        headers={"Connection": "close"}
    ) as session:
        results = await process_endpoints(session, MONITORED_ENDPOINTS)
        for result in results:
            health_data["endpoints"][result["name"]] = result
            if result["status"] == "ok":
                health_data["healthy_endpoints"] += 1
            else:
                health_data["degraded_endpoints"] += 1
    
    health_data["status"] = "ok" if health_data["degraded_endpoints"] == 0 else "degraded"
    return health_data