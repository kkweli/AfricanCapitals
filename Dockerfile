# --- Builder Stage ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Now copy the rest of the code
COPY . .

# Remove Python cache after copying all code
RUN find . -type d -name '__pycache__' -exec rm -rf {} + && \
    find . -type f -name '*.pyc' -delete

# --- Final Stage: Distroless ---
FROM gcr.io/distroless/python3

WORKDIR /app

COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/usr/local/lib/python3.11/site-packages \
    TZ=Etc/UTC

ENTRYPOINT ["/usr/bin/python3", "-m", "uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000"]