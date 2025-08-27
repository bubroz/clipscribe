# ClipScribe Production Deployment Guide v2.43.0

## 🚀 Production Deployment Overview

This guide covers the production deployment of ClipScribe with optimized Docker containers, comprehensive monitoring, and enterprise-grade configuration.

## 📋 Prerequisites

### System Requirements
- **Docker Engine**: 20.10+ with BuildKit enabled
- **Docker Compose**: 2.0+ with deploy support
- **Python**: 3.11+ (for local development)
- **Memory**: Minimum 4GB RAM, recommended 8GB+
- **Storage**: 10GB+ available space
- **Network**: Stable internet connection for API calls

### Required Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional but recommended for enterprise
VERTEX_AI_PROJECT=your_vertex_ai_project_id
GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/service-account.json
GCS_BUCKET=your_gcs_bucket_name
```

## 🏗️ Quick Start Deployment

### 1. Clone and Setup
```bash
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe

# Copy production environment template
cp env.production.example .env

# Edit with your production values
nano .env
```

### 2. Validate Configuration
```bash
# Run production validator
python scripts/validate_production.py

# Or using Poetry
poetry run clipscribe-validate
```

### 3. Deploy Services
```bash
# Deploy all services
./scripts/deploy.sh deploy all

# Or deploy individual components
./scripts/deploy.sh deploy cli    # CLI only (~400MB)
./scripts/deploy.sh deploy api    # API + Redis (~600MB)
./scripts/deploy.sh deploy web    # Web interface (~1.2GB)
```

### 4. Verify Deployment
```bash
# Check service status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs api
./scripts/deploy.sh logs web

# Run health checks
./scripts/deploy.sh health
```

## 🏛️ Service Architecture

### Multi-Stage Docker Build
```
📦 Production Images:
├── clipscribe-cli    (~400MB) - CLI-only, minimal
├── clipscribe-api    (~600MB) - API + Redis + Supervisor
└── clipscribe-web    (~1.2GB) - Full web interface

🔧 Build Stages:
├── builder          - Dependency installation
├── cli              - CLI with runtime dependencies
├── api              - API with additional services
└── web              - Web with all features
```

### Service Dependencies
```
🌐 External Access (Ports)
├── 80/443    → Nginx (reverse proxy)
├── 8000      → FastAPI (direct API access)
├── 8080      → Streamlit (direct web access)
└── 6379      → Redis (internal only)

🔗 Service Communication
├── clipscribe-web  → clipscribe-api
├── clipscribe-api  → redis
└── clipscribe-cli  → external APIs
```

## ⚙️ Configuration Management

### Environment Variables
```bash
# Application
CLIPSCRIBE_LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
PYTHONPATH=/app/src

# API Configuration
WORKER_TIMEOUT=3600
MAX_WORKERS=4
REDIS_URL=redis://redis:6379

# Resource Limits
MEMORY_LIMIT=2G
CPU_LIMIT=2.0

# Security
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=your-domain.com
```

### Docker Compose Overrides
Create `docker-compose.prod.yml` for production overrides:
```yaml
version: '3.8'

services:
  clipscribe-api:
    environment:
      - CLIPSCRIBE_LOG_LEVEL=WARNING
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'

  redis:
    environment:
      - REDIS_MAXMEMORY=512mb
```

## 🔒 Security Configuration

### Container Security
- ✅ Non-root user execution
- ✅ Minimal base images (python:3.12-slim)
- ✅ Security package updates
- ✅ No privileged containers
- ✅ Resource limits enforced

### Network Security
```yaml
# docker-compose.yml includes
services:
  nginx:
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/ssl/certs:ro
```

### Secrets Management
```bash
# Use Docker secrets or external secret managers
echo "your-secret-key" | docker secret create clipscribe_secret_key -

# Or use environment files
# .env (gitignored)
GOOGLE_API_KEY=your_key_here
SECRET_KEY=your_secret_here
```

## 📊 Monitoring and Observability

### Health Checks
```bash
# Built-in health endpoints
curl http://localhost:8000/docs          # API docs
curl http://localhost:8080/_stcore/health # Web health
redis-cli ping                           # Redis health
```

### Production Monitoring
```bash
# Start continuous monitoring
python scripts/monitor_production.py

# Or run one-time health check
python scripts/monitor_production.py --once

# Monitor with custom log file
python scripts/monitor_production.py --log-file /var/log/clipscribe/health.json
```

### Log Aggregation
```bash
# View service logs
docker-compose logs -f clipscribe-api
docker-compose logs -f clipscribe-web

# Follow all logs
docker-compose logs -f

# Export logs for analysis
docker-compose logs > production_logs.txt
```

## 🔄 Deployment Strategies

### Blue-Green Deployment
```bash
# Deploy new version alongside existing
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d clipscribe-api-new

# Test new version
curl http://localhost:8001/docs

# Switch traffic (update nginx config)
docker-compose restart nginx

# Remove old version
docker-compose stop clipscribe-api
docker-compose rm clipscribe-api
```

### Rolling Updates
```bash
# Update with zero downtime
docker-compose pull
docker-compose up -d --no-deps clipscribe-api
```

### Backup and Recovery
```bash
# Backup configuration
cp .env .env.backup
cp docker-compose.yml docker-compose.backup.yml

# Backup data volumes
docker run --rm -v clipscribe_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz /data

# Restore from backup
docker run --rm -v clipscribe_redis_data:/data -v $(pwd):/backup alpine tar xzf /backup/redis_backup.tar.gz -C /
```

## 🚨 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check container logs
docker-compose logs clipscribe-api

# Validate configuration
docker-compose config

# Check resource usage
docker stats
```

#### API Returns 500 Errors
```bash
# Check API logs
docker-compose logs clipscribe-api

# Test API endpoints
curl http://localhost:8000/docs

# Check Redis connectivity
docker-compose exec redis redis-cli ping
```

#### Memory Issues
```bash
# Check memory usage
docker stats

# Adjust memory limits
# docker-compose.yml
services:
  clipscribe-api:
    deploy:
      resources:
        limits:
          memory: 3G  # Increase limit
```

#### SSL/TLS Issues
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Mount certificates
# docker-compose.yml
volumes:
  - ./ssl:/etc/ssl/certs:ro
```

### Performance Tuning

#### Redis Optimization
```yaml
redis:
  environment:
    - REDIS_MAXMEMORY=512mb
    - REDIS_MAXMEMORY_POLICY=allkeys-lru
  command: ["redis-server", "--maxmemory", "512mb", "--maxmemory-policy", "allkeys-lru"]
```

#### API Performance
```yaml
clipscribe-api:
  environment:
    - WORKER_TIMEOUT=3600
    - MAX_WORKERS=8  # Adjust based on CPU cores
  deploy:
    resources:
      limits:
        cpus: '2.0'
```

## 📈 Scaling Strategies

### Horizontal Scaling
```yaml
# Scale API service
docker-compose up -d --scale clipscribe-api=3

# Use load balancer
# nginx.conf
upstream clipscribe_api {
    server clipscribe-api:8000;
    server clipscribe-api-2:8000;
    server clipscribe-api-3:8000;
}
```

### Vertical Scaling
```yaml
# Increase resources
clipscribe-api:
  deploy:
    resources:
      limits:
        memory: 4G
        cpus: '4.0'
```

## 🔧 Maintenance Tasks

### Regular Updates
```bash
# Update base images
docker-compose pull

# Rebuild and redeploy
docker-compose build --no-cache
docker-compose up -d

# Clean up old images
docker image prune -f
```

### Database Maintenance
```bash
# Redis maintenance
docker-compose exec redis redis-cli
> FLUSHDB  # Clear all data (if needed)
> SAVE     # Force save to disk
```

### Log Rotation
```bash
# Configure log rotation in docker-compose.yml
services:
  clipscribe-api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 📞 Support and Monitoring

### Alert Configuration
```bash
# Set up alerts for key metrics
# Example: Memory usage > 80%
# Example: API response time > 5s
# Example: Error rate > 1%

# Use monitoring tools like Prometheus + Grafana
# Or set up simple email alerts
```

### Emergency Procedures
```bash
# Quick restart all services
docker-compose restart

# Emergency stop
docker-compose down

# Force rebuild (nuclear option)
docker-compose down
docker system prune -f
docker-compose up -d --build
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Redis Documentation](https://redis.io/documentation/)

---

## 🎯 Next Steps

1. **Deploy to staging** - Test with production-like data
2. **Performance testing** - Load test with realistic workloads
3. **Security audit** - Review for production security requirements
4. **Monitoring setup** - Configure alerts and dashboards
5. **Documentation** - Update API and deployment documentation

For issues or questions, please refer to:
- [GitHub Issues](https://github.com/bubroz/clipscribe/issues)
- [Documentation](https://github.com/bubroz/clipscribe/tree/main/docs)
- [Production Scripts](https://github.com/bubroz/clipscribe/tree/main/scripts)

---

*ClipScribe v2.43.0 - Enterprise-ready video intelligence platform* 🚀
