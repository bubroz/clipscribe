# ClipScribe Optimized Multi-Stage Dockerfile
# Build stage for dependency installation
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure poetry for containerized builds
RUN poetry config virtualenvs.create false && \
    poetry config virtualenvs.in-project false

# Pre-install core dependencies (always required)
RUN poetry install --no-interaction --no-ansi --no-dev --only main

# Cache the virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies into virtual environment
RUN poetry install --no-interaction --no-ansi --no-dev --only main

# Production stage - CLI only (smallest)
FROM python:3.12-slim as cli

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create output directories
RUN mkdir -p output logs

# Default command for CLI
CMD ["clipscribe", "--help"]

# Production stage - API server
FROM cli as api

# Install additional API dependencies
RUN apt-get update && apt-get install -y \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Expose API port
EXPOSE 8000

# Health check for API
HEALTHCHECK CMD curl --fail http://localhost:8000/docs || exit 1

# Run API server
CMD ["uvicorn", "clipscribe.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

# Production stage - Web interface (largest, includes all dependencies)
FROM python:3.12-slim as web

# Install all system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure poetry
RUN poetry config virtualenvs.create false

# Install ALL dependencies for web interface
RUN poetry install --no-interaction --no-ansi --no-dev

# Copy application code
COPY . .

# Create output directories
RUN mkdir -p output logs

# Expose web interface port
EXPOSE 8080

# Environment variables for web interface
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Health check for web interface
HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# Run Streamlit web interface
CMD streamlit run streamlit_app/ClipScribe_Mission_Control.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.fileWatcherType=none \
    --browser.gatherUsageStats=false \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
