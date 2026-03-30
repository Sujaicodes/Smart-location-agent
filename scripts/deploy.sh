#!/bin/bash
# deploy.sh — Build and deploy both services to Cloud Run
# Usage: ./scripts/deploy.sh

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"your-gcp-project-id"}
REGION=${GCP_REGION:-"us-central1"}
MCP_SERVICE="location-mcp-server"
AGENT_SERVICE="location-agent"

echo "=== Deploying Smart Location Intelligence Agent ==="
echo "Project: $PROJECT_ID | Region: $REGION"

# ── Deploy MCP Server ───────────────────────────────────────────────
echo ""
echo ">>> Building MCP Server image..."
gcloud builds submit \
  --tag "gcr.io/$PROJECT_ID/$MCP_SERVICE" \
  --dockerfile mcp_server/Dockerfile \
  .

echo ">>> Deploying MCP Server to Cloud Run..."
gcloud run deploy "$MCP_SERVICE" \
  --image "gcr.io/$PROJECT_ID/$MCP_SERVICE" \
  --platform managed \
  --region "$REGION" \
  --no-allow-unauthenticated \
  --set-env-vars "USE_MOCK=false,GCP_PROJECT_ID=$PROJECT_ID" \
  --service-account "mcp-server-sa@$PROJECT_ID.iam.gserviceaccount.com"

MCP_URL=$(gcloud run services describe "$MCP_SERVICE" \
  --platform managed --region "$REGION" \
  --format "value(status.url)")

echo ">>> MCP Server deployed at: $MCP_URL"

# ── Deploy Agent ────────────────────────────────────────────────────
echo ""
echo ">>> Building Agent image..."
gcloud builds submit \
  --tag "gcr.io/$PROJECT_ID/$AGENT_SERVICE" \
  --dockerfile Dockerfile \
  .

echo ">>> Deploying Agent to Cloud Run..."
gcloud run deploy "$AGENT_SERVICE" \
  --image "gcr.io/$PROJECT_ID/$AGENT_SERVICE" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "MCP_SERVER_URL=$MCP_URL,USE_IAM_AUTH=true,GCP_PROJECT_ID=$PROJECT_ID" \
  --service-account "agent-sa@$PROJECT_ID.iam.gserviceaccount.com"

AGENT_URL=$(gcloud run services describe "$AGENT_SERVICE" \
  --platform managed --region "$REGION" \
  --format "value(status.url)")

echo ""
echo "=== Deployment complete ==="
echo "Agent URL: $AGENT_URL"
echo "MCP Server URL: $MCP_URL"
