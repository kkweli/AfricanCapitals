# African Capitals API

A FastAPI application that provides information about African countries and their capital cities, grouped by region.

## Features

- Retrieves data from the REST Countries API
- Groups countries by region
- Provides health check endpoint
- Structured logging
- Docker support for easy deployment

## Project Structure

```
.
├── app/
│   ├── core/           # Core functionality (config, logging)
│   ├── middleware/     # Custom middleware
│   ├── routers/        # API route definitions
│   └── services/       # Business logic
├── .env.example        # Example environment variables
├── Dockerfile          # Docker configuration
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