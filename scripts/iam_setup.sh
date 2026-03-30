#!/bin/bash
# iam_setup.sh — Create service accounts and IAM bindings
# Run this once before deploy.sh

set -e
PROJECT_ID=${GCP_PROJECT_ID:-"your-gcp-project-id"}

echo "=== Setting up IAM for Smart Location Agent ==="

# Service account for MCP Server (needs BigQuery access)
gcloud iam service-accounts create mcp-server-sa \
  --display-name="MCP Server Service Account" \
  --project="$PROJECT_ID"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:mcp-server-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:mcp-server-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

# Service account for Agent (needs to call MCP Server)
gcloud iam service-accounts create agent-sa \
  --display-name="Agent Service Account" \
  --project="$PROJECT_ID"

# Allow agent-sa to invoke the MCP Cloud Run service
gcloud run services add-iam-policy-binding location-mcp-server \
  --member="serviceAccount:agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region="us-central1"

echo "=== IAM setup complete ==="
