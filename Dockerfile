# ClipScribe Dockerfile for Google Cloud Run
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files first (better caching)
COPY pyproject.toml poetry.lock ./

# Install Poetry and dependencies
RUN pip install --no-cache-dir poetry==1.8.3 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-dev

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p output logs

# Expose port (Cloud Run uses 8080)
EXPOSE 8080

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Health check endpoint
HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# Run Streamlit with Cloud Run compatible settings
CMD streamlit run streamlit_app/ClipScribe_Mission_Control.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.fileWatcherType=none \
    --browser.gatherUsageStats=false \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
