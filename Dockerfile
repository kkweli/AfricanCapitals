# --- Builder Stage ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Install Python dependencies into a target directory
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# --- Final Stage: Distroless Python ---
FROM gcr.io/distroless/python3-debian11

WORKDIR /app

# Copy installed dependencies and app code from builder
COPY --from=builder /install /usr/local
COPY --from=builder /app /app

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["/usr/bin/python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]