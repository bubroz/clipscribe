#!/bin/bash
# ClipScribe Production Deployment Script v2.43.0
# Optimized for production deployment with Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="clipscribe"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "Environment file '$ENV_FILE' not found. Copying from example..."
        if [ -f "env.production.example" ]; then
            cp env.production.example .env
            log_warning "Please edit .env file with your production values before running deployment."
            exit 1
        else
            log_error "Neither .env nor env.production.example found. Please create a .env file."
            exit 1
        fi
    fi

    log_success "Prerequisites check passed"
}

# Validate environment
validate_environment() {
    log_info "Validating environment configuration..."

    # Check required environment variables
    required_vars=("GOOGLE_API_KEY")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done

    log_success "Environment validation passed"
}

# Build Docker images
build_images() {
    local target="${1:-all}"

    case $target in
        "cli")
            log_info "Building CLI image..."
            docker-compose build clipscribe-cli
            ;;
        "api")
            log_info "Building API image..."
            docker-compose build clipscribe-api
            ;;
        "web")
            log_info "Building Web image..."
            docker-compose build clipscribe-web
            ;;
        "all")
            log_info "Building all images..."
            docker-compose build
            ;;
        *)
            log_error "Invalid build target: $target"
            log_info "Valid targets: cli, api, web, all"
            exit 1
            ;;
    esac

    log_success "Image build completed"
}

# Start services
start_services() {
    local target="${1:-all}"

    log_info "Starting services..."

    case $target in
        "cli")
            docker-compose up -d clipscribe-cli
            ;;
        "api")
            docker-compose up -d redis clipscribe-api
            ;;
        "web")
            docker-compose up -d clipscribe-web
            ;;
        "all")
            docker-compose up -d
            ;;
        *)
            log_error "Invalid target: $target"
            log_info "Valid targets: cli, api, web, all"
            exit 1
            ;;
    esac

    log_success "Services started"
}

# Stop services
stop_services() {
    log_info "Stopping services..."
    docker-compose down
    log_success "Services stopped"
}

# Show status
show_status() {
    log_info "Service status:"
    docker-compose ps
}

# Show logs
show_logs() {
    local service="${1:-all}"
    local lines="${2:-100}"

    if [ "$service" = "all" ]; then
        docker-compose logs --tail="$lines"
    else
        docker-compose logs --tail="$lines" "$service"
    fi
}

# Health check
health_check() {
    log_info "Running health checks..."

    # Wait for services to be ready
    sleep 10

    # Check API health
    if curl -f http://localhost:8000/docs &> /dev/null; then
        log_success "API service is healthy"
    else
        log_warning "API service is not responding"
    fi

    # Check Web interface health
    if curl -f http://localhost:8080/_stcore/health &> /dev/null; then
        log_success "Web interface is healthy"
    else
        log_warning "Web interface is not responding"
    fi

    # Check Redis health
    if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
        log_success "Redis is healthy"
    else
        log_warning "Redis is not responding"
    fi
}

# Cleanup
cleanup() {
    log_info "Cleaning up..."

    # Remove dangling images
    docker image prune -f

    # Remove unused volumes
    docker volume prune -f

    log_success "Cleanup completed"
}

# Deploy function
deploy() {
    local target="${1:-all}"

    log_info "Starting deployment process..."

    check_prerequisites
    validate_environment
    build_images "$target"
    stop_services
    start_services "$target"
    health_check

    log_success "Deployment completed successfully!"
    log_info "You can access:"
    log_info "  - API: http://localhost:8000"
    log_info "  - Web Interface: http://localhost:8080"
    log_info "  - CLI: docker-compose exec clipscribe-cli clipscribe --help"
}

# Main script logic
case "${1:-help}" in
    "build")
        check_prerequisites
        build_images "${2:-all}"
        ;;
    "start")
        check_prerequisites
        validate_environment
        start_services "${2:-all}"
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        check_prerequisites
        validate_environment
        stop_services
        start_services "${2:-all}"
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "${2:-all}" "${3:-100}"
        ;;
    "health")
        health_check
        ;;
    "cleanup")
        cleanup
        ;;
    "deploy")
        deploy "${2:-all}"
        ;;
    "help"|*)
        echo "ClipScribe Production Deployment Script v2.43.0"
        echo ""
        echo "Usage: $0 [command] [target]"
        echo ""
        echo "Commands:"
        echo "  build [cli|api|web|all]     Build Docker images"
        echo "  start [cli|api|web|all]     Start services"
        echo "  stop                        Stop all services"
        echo "  restart [cli|api|web|all]  Restart services"
        echo "  status                      Show service status"
        echo "  logs [service] [lines]      Show service logs"
        echo "  health                      Run health checks"
        echo "  cleanup                     Clean up Docker resources"
        echo "  deploy [cli|api|web|all]   Full deployment (build + start + health check)"
        echo "  help                        Show this help message"
        echo ""
        echo "Targets:"
        echo "  cli     CLI-only service (~400MB)"
        echo "  api     API server with Redis (~600MB)"
        echo "  web     Web interface (~1.2GB)"
        echo "  all     All services (default)"
        echo ""
        echo "Examples:"
        echo "  $0 deploy all              # Deploy all services"
        echo "  $0 logs api 50             # Show last 50 lines of API logs"
        echo "  $0 restart api             # Restart API service only"
        ;;
esac
