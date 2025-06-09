# --- Builder Stage ---
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    find . -type d -name '__pycache__' -exec rm -rf {} + && \
    find . -type f -name '*.pyc' -delete

COPY . .

# --- Final Stage: Distroless ---
FROM gcr.io/distroless/python3-debian11

WORKDIR /app

COPY --from=builder /app /app

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]