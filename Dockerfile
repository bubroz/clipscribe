# ClipScribe Optimized Multi-Stage Dockerfile v2.43.0

# --- Builder Stage ---
# This stage installs all Python dependencies into a virtual environment.
FROM python:3.12-slim as builder

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 -

# Create a virtual environment
ENV VENV_PATH="/opt/venv"
RUN python -m venv $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

# Copy project files
WORKDIR /app
COPY pyproject.toml poetry.lock README.md ./

# Install dependencies with Poetry
# --without dev installs all production dependencies, including optional groups like 'api' and 'web'
# --no-root prevents installing the clipscribe package itself, as we'll copy the source later
# --sync ensures the environment matches the lock file exactly
RUN poetry install --no-interaction --no-ansi --without dev --no-root --sync

# --- Base Stage ---
# This stage creates a common base for the final images, with the virtual environment.
FROM python:3.12-slim as base

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd -r clipscribe && useradd -r -g clipscribe clipscribe

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Set environment variables for all stages
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/src
ENV PYTHONOPTIMIZE=2

WORKDIR /app
USER clipscribe

# --- API Stage ---
FROM base as api

# Explicitly install API dependencies using pip to ensure they are available
USER root
RUN pip install --no-cache-dir fastapi uvicorn[standard] redis rq pydantic-settings google-cloud-storage google-cloud-tasks httpx

# Create required directories with proper permissions
RUN mkdir -p /app/output /app/logs /app/output/video_archive && \
    chown -R clipscribe:clipscribe /app

COPY --chown=clipscribe:clipscribe src ./src
USER clipscribe

# Set working directory
WORKDIR /app

# Expose the API port
EXPOSE 8000

# Health check for the API
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8000/docs || exit 1

# Command to run the API server
CMD ["uvicorn", "src.clipscribe.api.app:app", "--host", "0.0.0.0", "--port", "8000"]


# --- Web Stage ---
FROM base as web

# Copy the application source code and static files
USER root
RUN mkdir -p /app/static_web && chown -R clipscribe:clipscribe /app
COPY --chown=clipscribe:clipscribe src ./src
COPY --chown=clipscribe:clipscribe static_web ./static_web
USER clipscribe

# Set working directory
WORKDIR /app

# Expose the web server port
EXPOSE 8080

# Health check for the web server
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8080/ || exit 1

# Command to run the web server
CMD ["python3", "-m", "http.server", "8080", "--directory", "/app/static_web"]


# --- Worker Stage ---
FROM base as worker

# Explicitly install worker dependencies using pip
USER root
RUN pip install --no-cache-dir fastapi uvicorn[standard] redis rq pydantic-settings google-cloud-storage google-cloud-tasks httpx yt-dlp \
    google-generativeai pillow moviepy

# Create required directories with proper permissions
RUN mkdir -p /app/temp /app/logs /app/output && \
    chown -R clipscribe:clipscribe /app

COPY --chown=clipscribe:clipscribe src ./src
USER clipscribe

# Set working directory
WORKDIR /app

# Expose the worker port
EXPOSE 8080

# Health check for the worker
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8080/health || exit 1

# Command to run the worker server
CMD ["uvicorn", "src.clipscribe.api.worker_server:app", "--host", "0.0.0.0", "--port", "8080"]


# --- CLI Stage (for local development/testing) ---
FROM base as cli

# Copy the application source code
USER root
COPY --chown=clipscribe:clipscribe src ./src

# Create output directories with proper permissions
RUN mkdir -p /app/output /app/logs && \
    chown -R clipscribe:clipscribe /app/output /app/logs

USER clipscribe

# Set the entrypoint to the clipscribe CLI
ENTRYPOINT ["clipscribe"]
CMD ["--help"]
