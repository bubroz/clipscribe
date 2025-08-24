# Docker Optimization Guide

## Overview

ClipScribe's Docker images have been optimized to reduce build size from potential >8GiB to as low as ~500MB for CLI-only usage. This is achieved through multi-stage builds and optional dependency management.

## Build Stages

### CLI Stage (~500MB)
**Target**: `cli`
**Use Case**: Command-line interface only
**Includes**:
- Core dependencies (google-generativeai, pydantic, rich, etc.)
- Video processing capabilities
- Output formatting
- **Excludes**: ML libraries, web frameworks, API components

```bash
# Build CLI-only image
docker build --target cli -t clipscribe-cli .

# Run CLI
docker run -it --rm -v $(pwd)/output:/app/output clipscribe-cli
```

### API Stage (~800MB)
**Target**: `api`
**Use Case**: FastAPI server with Redis queue
**Includes**:
- All CLI dependencies
- FastAPI, Uvicorn
- Redis, RQ
- Enterprise features (optional)
- **Excludes**: ML libraries, web interface

```bash
# Build API image
docker build --target api -t clipscribe-api .

# Run API server
docker run -p 8000:8000 -e GOOGLE_API_KEY=your_key clipscribe-api
```

### Web Stage (~3GB+)
**Target**: `web`
**Use Case**: Full Streamlit web interface
**Includes**:
- All dependencies (ML, visualization, enterprise)
- Streamlit web interface
- Complete feature set

```bash
# Build web image
docker build --target web -t clipscribe-web .

# Run web interface
docker run -p 8080:8080 -e GOOGLE_API_KEY=your_key clipscribe-web
```

## Docker Compose Usage

Use the provided `docker-compose.yml` for easy deployment:

```bash
# Start CLI version
docker-compose up clipscribe-cli

# Start API with Redis
docker-compose up clipscribe-api redis

# Start web interface
docker-compose up clipscribe-web
```

## Dependency Optimization

### Core Dependencies (Always Included)
- `google-generativeai` - Gemini API client
- `pydantic` - Data validation
- `rich` - CLI formatting
- `yt-dlp` - Video downloading
- `click` - CLI framework

### Optional Dependencies (Install as needed)

#### ML Features (`poetry install -E ml`)
- `spacy` - NLP processing (~500MB)
- `transformers` - ML models (~500MB)
- `torch` - PyTorch (~2GB)
- `gliner` - Entity extraction

#### Enterprise Features (`poetry install -E enterprise`)
- `google-cloud-aiplatform` - Vertex AI
- `google-cloud-storage` - GCS integration

#### API Features (`poetry install -E api`)
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `redis` - Cache/queue
- `rq` - Job queue

#### Visualization (`poetry install -E viz`)
- `plotly` - Charts and graphs
- `pdfkit` - PDF generation

#### Web Interface (`poetry install -E web`)
- `streamlit` - Web application framework

## Performance Improvements

### Size Reduction
| Configuration | Old Size | New Size | Reduction |
|---------------|----------|----------|-----------|
| CLI Only | ~3GB+ | ~500MB | 83% smaller |
| API Server | ~3GB+ | ~800MB | 73% smaller |
| Full Web | ~8GB+ | ~3GB | 62% smaller |

### Build Time Optimization
- **Layer Caching**: Dependencies installed in separate layers
- **Multi-stage**: Build dependencies separate from runtime
- **Virtual Environment**: Isolated Python environment
- **Minimal Base Images**: `python:3.12-slim` instead of full images

### Runtime Optimization
- **Lazy Loading**: Optional dependencies loaded on-demand
- **Memory Efficient**: Only required components loaded
- **Faster Startup**: Reduced import overhead

## Usage Examples

### Development
```bash
# Install only core dependencies for development
poetry install --only main,dev

# Install with ML features for testing
poetry install -E ml --only main,dev,test
```

### Production Deployment
```bash
# CLI-only deployment
docker build --target cli -t clipscribe-cli .
docker run clipscribe-cli process video "URL"

# API deployment with Redis
docker-compose up clipscribe-api redis

# Full web deployment
docker-compose up clipscribe-web
```

### CI/CD Optimization
```yaml
# GitHub Actions example
- name: Build CLI Image
  run: docker build --target cli -t clipscribe-cli .

- name: Build API Image
  run: docker build --target api -t clipscribe-api .

- name: Build Web Image
  run: docker build --target web -t clipscribe-web .
```

## Migration Guide

### From Old Dockerfile
1. **Update build commands**: Use `--target` parameter
2. **Adjust volume mounts**: Update paths if needed
3. **Environment variables**: Ensure all required vars are set
4. **Port mappings**: Use correct ports (8000 for API, 8080 for web)

### From Poetry Install
```bash
# Old way (installs everything)
poetry install

# New way (install only what you need)
poetry install --only main,dev  # Core + dev tools
poetry install -E api,enterprise  # Add API and cloud features
```

## Troubleshooting

### Build Issues
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker build --no-cache --target cli .

# Check image size
docker images clipscribe-cli
```

### Runtime Issues
```bash
# Check if optional dependencies are missing
docker run clipscribe-cli python -c "import sys; print(sys.path)"

# Verify environment variables
docker run clipscribe-cli env | grep GOOGLE_API_KEY
```

### Performance Monitoring
```bash
# Check container resource usage
docker stats clipscribe-cli

# Monitor memory usage
docker run clipscribe-cli python -c "import psutil; print(f'Memory: {psutil.virtual_memory()}')"
```

## Future Optimizations

1. **Distroless Images**: Further size reduction using distroless base
2. **Multi-architecture**: Support for ARM64 and other architectures
3. **Dependency Auditing**: Automated checking for unused dependencies
4. **Layer Optimization**: Further optimization of Docker layer structure
