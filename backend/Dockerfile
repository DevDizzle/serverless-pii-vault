FROM python:3.11-slim

# Install system dependencies for pdf2image (poppler) and psycopg2
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variables will be injected by Cloud Run / Docker Compose
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
