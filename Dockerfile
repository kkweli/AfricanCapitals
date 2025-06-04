# --- Builder Stage ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Copy only requirements first for better cache usage
COPY requirements.txt .

# Install dependencies to a target directory
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# Remove build dependencies to keep builder image small (optional)
RUN apt-get purge -y --auto-remove gcc && rm -rf /var/lib/apt/lists/*

# Copy application code (after dependencies for better cache)
COPY . .

# --- Final Stage: Distroless Python ---
FROM gcr.io/distroless/python3-debian11

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local
COPY --from=builder /app /app

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Etc/UTC

CMD ["run.py"]