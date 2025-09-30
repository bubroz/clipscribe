#!/bin/bash
# Docker-based testing to avoid timeout issues

echo "Building ClipScribe test container..."
docker build -t clipscribe-test -f Dockerfile.test .

echo "Running tests in Docker container..."
docker run --rm \
  -e MISTRAL_API_KEY="$MISTRAL_API_KEY" \
  -e XAI_API_KEY="$XAI_API_KEY" \
  -v "$(pwd)/output:/app/output" \
  clipscribe-test \
  python scripts/test_voxtral_grok_integration.py

echo "Test completed. Check output/ directory for results."
