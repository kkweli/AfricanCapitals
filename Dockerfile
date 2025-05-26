# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies (required for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev

# Install application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Install Uvicorn explicitly (required for FastAPI)
RUN pip install uvicorn[standard]

# Expose port
EXPOSE 8000

# Run the FastAPI app with proper configuration
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]