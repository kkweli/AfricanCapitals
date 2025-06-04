# --- Builder Stage ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Copy requirements and install to a target directory
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# --- Final Stage: Distroless Python ---
FROM gcr.io/distroless/python3-debian11

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local
COPY --from=builder /app /app

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Etc/UTC

# Run the application
CMD ["run.py"]