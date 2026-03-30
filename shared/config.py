"""
Shared configuration for Smart Location Intelligence Agent.
In production, load these from environment variables or Secret Manager.
"""

import os

# --- GCP Config ---
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-gcp-project-id")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", "location_intelligence")
BIGQUERY_TABLE = os.environ.get("BIGQUERY_TABLE", "locations")

# --- MCP Server Config ---
MCP_SERVER_URL = os.environ.get(
    "MCP_SERVER_URL", "http://localhost:8080"
)  # Cloud Run URL in prod
MCP_SERVER_PORT = int(os.environ.get("MCP_SERVER_PORT", "8080"))

# --- External APIs ---
# Geocoding: OpenStreetMap Nominatim (free, no key required)

# --- Agent Config ---
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
AGENT_NAME = "SmartLocationAgent"
AGENT_DESCRIPTION = (
    "An AI-powered tour guide that retrieves location and animal data from "
    "SQLite/BigQuery via MCP, enriches it with OpenStreetMap and Wikipedia, and "
    "synthesizes a conversational narrative for the user."
)

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK_DATA_PATH = os.path.join(BASE_DIR, "data", "mock_locations.json")
SQLITE_DB_PATH = os.path.join(BASE_DIR, "data", "locations.db")
