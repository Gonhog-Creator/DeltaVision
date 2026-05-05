# Multi-stage Dockerfile for DeltaVision

# Base stage
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libatk1.0-0 \
    libgcc-s1 \
    && rm -rf /var/lib/apt/lists/*

# Development stage
FROM base as development

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/{raw_video,processed,exports} logs

# Set permissions
RUN chmod +x app/main.py

# Expose port
EXPOSE 8000

# Default command for development
CMD ["python", "app/main.py", "serve", "--reload"]

# API stage
FROM base as api

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY configs/ ./configs/

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p data/{raw_video,processed,exports} logs

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# API command
CMD ["python", "app/main.py", "serve"]

# Worker stage
FROM base as worker

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY configs/ ./configs/

# Create necessary directories
RUN mkdir -p data/{raw_video,processed,exports} logs

# Create non-root user
RUN useradd --create-home --shell /bin/bash worker && \
    chown -R worker:worker /app
USER worker

# Worker command
CMD ["python", "app/main.py", "process-folder", "/app/vids"]

# Production stage
FROM api as production

# Additional production optimizations
ENV LOG_LEVEL=WARNING \
    API_DEBUG=false

# Production command
CMD ["gunicorn", "app.api.server:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
