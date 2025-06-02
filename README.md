# African Capitals API with WebGL Map Visualization

A FastAPI application that provides information about African countries and their capital cities, with an interactive WebGL map visualization and economic data.

## Features

- Retrieves data from the REST Countries API and World Bank API
- Interactive WebGL map showing African countries and capitals
- Economic data including GDP, population, and key sectors
- Country-specific detailed profiles with visualizations
- Caching with Redis for improved performance
- Structured logging and error handling
- Docker support for easy deployment

## Project Structure

```
.
├── app/
│   ├── cache/          # Cache directory for GeoJSON data
│   ├── core/           # Core functionality (config, logging)
│   ├── middleware/     # Custom middleware
│   ├── routers/        # API route definitions
│   ├── services/       # Business logic
│   └── static/         # WebGL frontend files
│       ├── index.html  # Main HTML page
│       └── js/         # JavaScript files for WebGL map
├── .env.example        # Example environment variables
��── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
├── requirements.txt    # Python dependencies
└── run.py              # Application entry point
```

## Getting Started

### Prerequisites

- Python 3.9+
- Docker (optional)

### Local Development

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file from the example:
   ```
   cp .env.example .env
   ```
5. Run the application:
   ```
   python run.py
   ```

### Docker Deployment

1. Build and run with Docker Compose:
   ```
   docker-compose up -d
   ```

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /african-capitals` - Get African countries and their capitals grouped by region
- `GET /api/v1/economic-data` - Get economic data for all African countries
- `GET /api/v1/economic-data/{country_code}` - Get economic data for a specific country
- `GET /api/v1/map-data` - Get GeoJSON data for all African countries
- `GET /api/v1/map-data/{country_code}` - Get GeoJSON data for a specific country
- `GET /api/v1/country-profile/{country_code}` - Get comprehensive profile for a specific country

## WebGL Map Visualization

The application includes an interactive WebGL map that visualizes:

- African countries with their boundaries
- Capital cities with markers
- Economic data with hover tooltips
- Detailed country profiles with key sector breakdowns

To access the map, simply open the root URL in your browser after starting the application.

## Scaling and Production Readiness

This API has been designed with the following production-ready features:

- Structured logging with request IDs
- Proper error handling and timeouts
- Environment-based configuration
- Docker containerization
- Health checks
- Separation of concerns (routers, services, etc.)

Future phases will include:
- Caching with Redis
- Rate limiting
- Authentication
- Metrics collection
- Horizontal scaling support