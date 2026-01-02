#!/bin/bash
# AIKU Backend - Google Cloud Run Deployment Script
# Usage: ./deploy.sh [PROJECT_ID]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${1:-aiku-travel-agent}"
REGION="europe-west1"
SERVICE_NAME="aiku-backend"
REPO_NAME="aiku"

echo -e "${GREEN}=== AIKU Backend Deployment ===${NC}"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    exit 1
fi

# Set project
echo -e "${YELLOW}Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com

# Create Artifact Registry repository if not exists
echo -e "${YELLOW}Creating Artifact Registry repository...${NC}"
gcloud artifacts repositories describe $REPO_NAME --location=$REGION 2>/dev/null || \
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="AIKU Docker images"

# Configure Docker to use Artifact Registry
echo -e "${YELLOW}Configuring Docker authentication...${NC}"
gcloud auth configure-docker $REGION-docker.pkg.dev --quiet

# Create secrets in Secret Manager (if not exists)
echo -e "${YELLOW}Setting up secrets in Secret Manager...${NC}"

create_secret_if_not_exists() {
    local secret_name=$1
    local secret_value=$2

    if ! gcloud secrets describe $secret_name --project=$PROJECT_ID &>/dev/null; then
        echo "Creating secret: $secret_name"
        echo -n "$secret_value" | gcloud secrets create $secret_name \
            --data-file=- \
            --replication-policy=automatic \
            --project=$PROJECT_ID
    else
        echo "Secret already exists: $secret_name"
    fi
}

# Check if .env exists and source it
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)

    # Create secrets from .env values
    [ -n "$SUPABASE_URL" ] && create_secret_if_not_exists "aiku-supabase-url" "$SUPABASE_URL"
    [ -n "$SUPABASE_ANON_KEY" ] && create_secret_if_not_exists "aiku-supabase-anon-key" "$SUPABASE_ANON_KEY"
    [ -n "$SUPABASE_SERVICE_ROLE_KEY" ] && create_secret_if_not_exists "aiku-supabase-service-role-key" "$SUPABASE_SERVICE_ROLE_KEY"
    [ -n "$ANTHROPIC_API_KEY" ] && create_secret_if_not_exists "aiku-anthropic-api-key" "$ANTHROPIC_API_KEY"
    [ -n "$FLIGHTS_API_KEY" ] && create_secret_if_not_exists "aiku-flights-api-key" "$FLIGHTS_API_KEY"
else
    echo -e "${YELLOW}Warning: .env file not found. Make sure secrets are already configured in Secret Manager.${NC}"
fi

# Grant Cloud Run access to secrets
echo -e "${YELLOW}Granting Cloud Run access to secrets...${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
COMPUTE_SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

for secret in aiku-supabase-url aiku-supabase-anon-key aiku-supabase-service-role-key aiku-anthropic-api-key aiku-flights-api-key; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:$COMPUTE_SA" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID 2>/dev/null || true
done

# Build and push Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
IMAGE_TAG="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/backend:$(date +%Y%m%d-%H%M%S)"
IMAGE_LATEST="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/backend:latest"

docker build -t $IMAGE_TAG -t $IMAGE_LATEST .

echo -e "${YELLOW}Pushing Docker image...${NC}"
docker push $IMAGE_TAG
docker push $IMAGE_LATEST

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE_TAG \
    --region=$REGION \
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
    --set-secrets="FLIGHTS_API_KEY=aiku-flights-api-key:latest"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo -e "Service URL: ${GREEN}$SERVICE_URL${NC}"
echo ""
echo "Test the deployment:"
echo "  curl $SERVICE_URL/health"
echo "  curl $SERVICE_URL/api/v1/health"
