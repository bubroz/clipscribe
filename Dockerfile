# ClipScribe Multi-Stage Dockerfile
# Supports multiple targets: api, cli, web

# ============================================================================
# Base Stage: Python + Poetry Setup
# ============================================================================
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=0 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install system dependencies required for building Python packages
# - build-essential: C compiler and build tools (needed for packages with C extensions)
# - curl: For downloading Poetry installer
# - git: Some packages may need git during installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

# Set working directory
WORKDIR /app

# ============================================================================
# Dependencies Stage: Install Python Dependencies
# ============================================================================
FROM base AS dependencies

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure Poetry: Don't create virtualenv (we're in a container)
# Install dependencies with api and enterprise extras (for GCS, FastAPI, etc.)
# Note: We use --no-root here because we copy source code separately in target stages
# This allows better Docker layer caching
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-root -E api -E enterprise && \
    rm -rf ${POETRY_CACHE_DIR}

# ============================================================================
# API Target: FastAPI Service for Cloud Run
# ============================================================================
FROM dependencies AS api

# Copy source code, pyproject.toml, and README.md (needed to install the package)
COPY src/ ./src/
COPY pyproject.toml README.md ./

# Install the clipscribe package itself (dependencies already installed in previous stage)
# Poetry will recognize dependencies are already installed and just install the root package
RUN poetry install --no-dev --no-interaction -E api -E enterprise && \
    rm -rf ${POETRY_CACHE_DIR}

# Set PYTHONPATH so Python can find the clipscribe package
ENV PYTHONPATH=/app/src

# Expose port (Cloud Run will set PORT env var, but 8000 is standard)
EXPOSE 8000

# Health check endpoint (Cloud Run will use this for readiness checks)
# Note: /v1/health exists but requires auth, so we use a simple Python check
# Cloud Run has its own health checking mechanism
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost', int('${PORT:-8000}'))); s.close()" || exit 1

# Run uvicorn with the FastAPI app
# Cloud Run sets PORT automatically, but we default to 8000
# Use 0.0.0.0 to bind to all interfaces (required for Cloud Run)
CMD ["sh", "-c", "uvicorn clipscribe.api.app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]

# ============================================================================
# CLI Target: Command-line interface (for future use)
# ============================================================================
FROM dependencies AS cli

# Copy source code
COPY src/ ./src/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Default entrypoint to clipscribe CLI
ENTRYPOINT ["python", "-m", "clipscribe.commands.cli"]

# ============================================================================
# Web Target: Streamlit web interface (for future use)
# ============================================================================
FROM dependencies AS web

# Install web extras (streamlit)
RUN poetry install --no-dev --no-interaction --no-root -E web && \
    rm -rf ${POETRY_CACHE_DIR}

# Copy source code
COPY src/ ./src/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8080

# Run Streamlit
CMD ["sh", "-c", "streamlit run src/clipscribe/web/app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true"]

