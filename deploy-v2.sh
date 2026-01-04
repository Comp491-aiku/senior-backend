#!/bin/bash
#
# AIKU Backend - Cloud Run Deployment Script v2
#
# Usage:
#   ./deploy-v2.sh              # Full deployment (build + push + deploy)
#   ./deploy-v2.sh build        # Build Docker image only
#   ./deploy-v2.sh push         # Push image to registry
#   ./deploy-v2.sh deploy       # Deploy to Cloud Run (uses latest image)
#   ./deploy-v2.sh logs         # View recent logs
#   ./deploy-v2.sh rollback     # Rollback to previous revision
#   ./deploy-v2.sh status       # Check service status
#
# Environment variables:
#   PROJECT_ID   - GCP project ID (default: aiku-travel-agent)
#   REGION       - GCP region (default: europe-west1)
#   ENV          - Environment: dev, staging, prod (default: prod)
#

set -e

# =============================================================================
# Configuration
# =============================================================================

PROJECT_ID="${PROJECT_ID:-aiku-backend}"
REGION="${REGION:-europe-west1}"
ENV="${ENV:-prod}"

SERVICE_NAME="aiku-backend"
REPO_NAME="aiku"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Image tags
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_REGISTRY="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME"
IMAGE_NAME="backend"
IMAGE_TAG="$IMAGE_REGISTRY/$IMAGE_NAME:$TIMESTAMP"
IMAGE_LATEST="$IMAGE_REGISTRY/$IMAGE_NAME:latest"

# gcloud path (handle local vs system installation)
GCLOUD_PATH="${GCLOUD_PATH:-gcloud}"
if command -v /Users/ilkeryoru/Desktop/aiku/google-cloud-sdk/bin/gcloud &> /dev/null; then
    GCLOUD_PATH="/Users/ilkeryoru/Desktop/aiku/google-cloud-sdk/bin/gcloud"
fi

# =============================================================================
# Colors & Logging
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "\n${CYAN}=== $1 ===${NC}"; }

# =============================================================================
# Pre-flight Checks
# =============================================================================

preflight_check() {
    log_step "Pre-flight Checks"

    # Check gcloud
    if ! command -v "$GCLOUD_PATH" &> /dev/null; then
        log_error "gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    log_info "gcloud CLI: $($GCLOUD_PATH --version | head -1)"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Install from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    log_info "Docker: $(docker --version)"

    # Check authentication
    if ! $GCLOUD_PATH auth list --filter="status:ACTIVE" --format="value(account)" | head -1 | grep -q "@"; then
        log_error "Not authenticated with gcloud. Run: gcloud auth login"
        exit 1
    fi
    log_info "Authenticated as: $($GCLOUD_PATH auth list --filter='status:ACTIVE' --format='value(account)' | head -1)"

    # Check project access
    if ! $GCLOUD_PATH projects describe "$PROJECT_ID" &> /dev/null; then
        log_error "Cannot access project: $PROJECT_ID"
        exit 1
    fi
    log_info "Project: $PROJECT_ID"

    # Check Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    log_info "Docker daemon: Running"

    # Check we're in the right directory
    if [[ ! -f "$SCRIPT_DIR/Dockerfile" ]]; then
        log_error "Dockerfile not found in $SCRIPT_DIR"
        exit 1
    fi
    log_info "Dockerfile: Found"

    # Check requirements.txt
    if [[ ! -f "$SCRIPT_DIR/requirements.txt" ]]; then
        log_error "requirements.txt not found"
        exit 1
    fi
    log_info "requirements.txt: Found"

    log_success "All pre-flight checks passed"
}

# =============================================================================
# Setup & Configuration
# =============================================================================

setup_gcp() {
    log_step "Configuring GCP"

    # Set project
    $GCLOUD_PATH config set project "$PROJECT_ID" --quiet

    # Configure Docker for Artifact Registry
    $GCLOUD_PATH auth configure-docker "$REGION-docker.pkg.dev" --quiet

    log_success "GCP configured"
}

# =============================================================================
# Build Functions
# =============================================================================

build_image() {
    log_step "Building Docker Image"

    cd "$SCRIPT_DIR"

    log_info "Building: $IMAGE_TAG"
    log_info "Platform: linux/amd64"

    # Build for Cloud Run (linux/amd64)
    docker build \
        --platform linux/amd64 \
        -t "$IMAGE_TAG" \
        -t "$IMAGE_LATEST" \
        .

    # Show image size
    SIZE=$(docker images "$IMAGE_TAG" --format "{{.Size}}")
    log_success "Image built successfully (Size: $SIZE)"
}

# =============================================================================
# Push Functions
# =============================================================================

push_image() {
    log_step "Pushing Image to Artifact Registry"

    log_info "Pushing: $IMAGE_TAG"
    docker push "$IMAGE_TAG"

    log_info "Pushing: $IMAGE_LATEST"
    docker push "$IMAGE_LATEST"

    log_success "Image pushed successfully"
}

# =============================================================================
# Deploy Functions
# =============================================================================

deploy_service() {
    log_step "Deploying to Cloud Run"

    local image="${1:-$IMAGE_LATEST}"

    log_info "Service: $SERVICE_NAME"
    log_info "Image: $image"
    log_info "Region: $REGION"

    $GCLOUD_PATH run deploy "$SERVICE_NAME" \
        --image="$image" \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --memory=1Gi \
        --cpu=1 \
        --timeout=300 \
        --concurrency=80 \
        --min-instances=0 \
        --max-instances=10 \
        --set-env-vars="APP_ENV=production,APP_DEBUG=false,LLM_MAX_ITERATIONS=25" \
        --set-env-vars="WEATHER_AGENT_URL=https://weather-agent-seven.vercel.app" \
        --set-env-vars="FLIGHT_AGENT_URL=https://flight-agent.vercel.app" \
        --set-env-vars="HOTEL_AGENT_URL=https://hotel-agent-delta.vercel.app" \
        --set-env-vars="TRANSFER_AGENT_URL=https://transfer-agent.vercel.app" \
        --set-env-vars="ACTIVITIES_AGENT_URL=https://activities-agent.vercel.app" \
        --set-env-vars="EXCHANGE_AGENT_URL=https://exchange-agent.vercel.app" \
        --set-env-vars="UTILITY_AGENT_URL=https://utility-agent.vercel.app" \
        --set-env-vars="FLIGHTS_API_URL=https://fast-flights-api-1042410626896.europe-west1.run.app" \
        --set-secrets="SUPABASE_URL=aiku-supabase-url:latest" \
        --set-secrets="SUPABASE_ANON_KEY=aiku-supabase-anon-key:latest" \
        --set-secrets="SUPABASE_SERVICE_ROLE_KEY=aiku-supabase-service-role-key:latest" \
        --set-secrets="ANTHROPIC_API_KEY=aiku-anthropic-api-key:latest" \
        --set-secrets="FLIGHTS_API_KEY=aiku-flights-api-key:latest" \
        --quiet

    # Get service URL
    SERVICE_URL=$($GCLOUD_PATH run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")

    log_success "Deployment complete!"
    echo ""
    echo -e "  Service URL: ${GREEN}$SERVICE_URL${NC}"
    echo ""
}

# =============================================================================
# Utility Functions
# =============================================================================

view_logs() {
    log_step "Viewing Recent Logs"

    $GCLOUD_PATH run services logs read "$SERVICE_NAME" \
        --region="$REGION" \
        --limit=100
}

check_status() {
    log_step "Service Status"

    # Get service info
    $GCLOUD_PATH run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --format="table(
            status.url,
            status.conditions[0].status,
            spec.template.spec.containers[0].resources.limits.memory,
            spec.template.spec.containers[0].resources.limits.cpu,
            spec.template.metadata.annotations['autoscaling.knative.dev/minScale'],
            spec.template.metadata.annotations['autoscaling.knative.dev/maxScale']
        )"

    echo ""

    # Get recent revisions
    log_info "Recent Revisions:"
    $GCLOUD_PATH run revisions list \
        --service="$SERVICE_NAME" \
        --region="$REGION" \
        --limit=5 \
        --format="table(metadata.name,status.conditions[0].status,spec.containers[0].image:label=IMAGE)"
}

rollback_service() {
    log_step "Rolling Back to Previous Revision"

    # Get previous revision
    PREVIOUS=$($GCLOUD_PATH run revisions list \
        --service="$SERVICE_NAME" \
        --region="$REGION" \
        --limit=2 \
        --format="value(metadata.name)" | tail -1)

    if [[ -z "$PREVIOUS" ]]; then
        log_error "No previous revision found"
        exit 1
    fi

    log_info "Rolling back to: $PREVIOUS"

    $GCLOUD_PATH run services update-traffic "$SERVICE_NAME" \
        --region="$REGION" \
        --to-revisions="$PREVIOUS=100"

    log_success "Rollback complete"
}

health_check() {
    log_step "Health Check"

    SERVICE_URL=$($GCLOUD_PATH run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")

    log_info "Checking: $SERVICE_URL/health"

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health" --max-time 10)

    if [[ "$HTTP_CODE" == "200" ]]; then
        log_success "Health check passed (HTTP $HTTP_CODE)"
        curl -s "$SERVICE_URL/health" | python3 -m json.tool 2>/dev/null || true
    else
        log_error "Health check failed (HTTP $HTTP_CODE)"
        exit 1
    fi
}

# =============================================================================
# Full Deployment
# =============================================================================

full_deploy() {
    log_step "Full Deployment"
    echo ""
    echo "  Project:     $PROJECT_ID"
    echo "  Region:      $REGION"
    echo "  Service:     $SERVICE_NAME"
    echo "  Environment: $ENV"
    echo "  Timestamp:   $TIMESTAMP"
    echo ""

    preflight_check
    setup_gcp
    build_image
    push_image
    deploy_service "$IMAGE_TAG"
    health_check

    echo ""
    log_success "Full deployment completed successfully!"
}

# =============================================================================
# Main
# =============================================================================

show_help() {
    echo "AIKU Backend Deployment Script v2"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  (default)   Full deployment (build + push + deploy)"
    echo "  build       Build Docker image only"
    echo "  push        Push image to Artifact Registry"
    echo "  deploy      Deploy to Cloud Run (uses latest image)"
    echo "  logs        View recent service logs"
    echo "  status      Check service status and revisions"
    echo "  rollback    Rollback to previous revision"
    echo "  health      Run health check"
    echo "  help        Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  PROJECT_ID  GCP project ID (default: aiku-travel-agent)"
    echo "  REGION      GCP region (default: europe-west1)"
    echo "  ENV         Environment: dev, staging, prod (default: prod)"
    echo ""
}

case "${1:-full}" in
    build)
        preflight_check
        build_image
        ;;
    push)
        preflight_check
        setup_gcp
        push_image
        ;;
    deploy)
        preflight_check
        setup_gcp
        deploy_service "$IMAGE_LATEST"
        health_check
        ;;
    logs)
        view_logs
        ;;
    status)
        check_status
        ;;
    rollback)
        rollback_service
        ;;
    health)
        health_check
        ;;
    help|--help|-h)
        show_help
        ;;
    full|*)
        full_deploy
        ;;
esac
