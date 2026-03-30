# Smart Location Intelligence Agent

An AI-powered tour guide built with Google ADK + Gemini, using the **Model Context Protocol (MCP)** to securely query BigQuery for location data, enriched by OpenStreetMap and Wikipedia.

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────┐
│     ADK Agent (Gemini)          │  ← agent/agent.py
│  - Parses intent                │
│  - Orchestrates tools           │
│  - Synthesizes narrative        │
└────────┬───────────┬────────────┘
         │ MCP       │ Direct API
         ▼           ▼
┌──────────────┐  ┌──────────────────────────────────┐
│  MCP Server  │  │  External Tools                   │
│  (Cloud Run) │  │  - OpenStreetMap Nominatim (free) │
│  - BigQuery  │  │  - Wikipedia (free)               │
└──────────────┘  └──────────────────────────────────┘
```

---

## Quick Start (Local / Mock Mode)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the MCP Server

```bash
cd smart-location-agent
USE_MOCK=true python mcp_server/server.py
# Server runs at http://localhost:8080
```

### 3. Run the Agent

```bash
# Interactive REPL
python main.py

# Single query
python main.py --query "Tell me about animals near the Central Park Zoo"
```

> **No API keys needed in mock mode.** Add `GEMINI_API_KEY` to get real Gemini narratives.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `USE_MOCK` | `true` | Use local JSON instead of BigQuery |
| `MCP_SERVER_URL` | `http://localhost:8080` | URL of the MCP Server |
| `USE_IAM_AUTH` | `false` | Attach IAM ID token to MCP calls |
| `GEMINI_API_KEY` | `` | Gemini API key for narrative synthesis |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `GCP_PROJECT_ID` | `` | GCP project (for BigQuery + Cloud Run) |

> **No Google Maps API key needed!** Geocoding is handled by free OpenStreetMap Nominatim.

---

## Project Structure

```
smart-location-agent/
├── main.py                    # CLI entrypoint
├── requirements.txt
├── Dockerfile                 # Agent container
│
├── shared/
│   └── config.py              # Shared config + env vars
│
├── data/
│   └── mock_locations.json    # Mock BigQuery dataset
│
├── mcp_server/
│   ├── server.py              # FastAPI MCP Server
│   ├── requirements.txt
│   └── Dockerfile             # MCP Server container
│
├── agent/
│   ├── agent.py               # Core ADK Agent logic
│   ├── mcp_client.py          ← MCP Client (calls the server)
│   └── external_tools.py      # OpenStreetMap + Wikipedia tools
│
└── scripts/
    ├── deploy.sh              # Cloud Run deployment
    └── iam_setup.sh           # Service account + IAM setup
```

---

## Production Deployment (Cloud Run)

```bash
# 1. Set your project
export GCP_PROJECT_ID=your-project-id

# 2. Create service accounts + IAM bindings
bash scripts/iam_setup.sh

# 3. Deploy both services
bash scripts/deploy.sh
```

The MCP Server is deployed with `--no-allow-unauthenticated` — only the Agent's service account can invoke it via IAM.

---

## Switching to Real BigQuery

1. Set `USE_MOCK=false`
2. Create a BigQuery dataset and table matching the schema in `mock_locations.json`
3. Set `GCP_PROJECT_ID`, `BIGQUERY_DATASET`, `BIGQUERY_TABLE`
4. Ensure ADC or service account credentials are available

BigQuery schema:
```sql
CREATE TABLE location_intelligence.locations (
  id STRING,
  name STRING,
  type STRING,
  habitat STRING,
  location_name STRING,
  lat FLOAT64,
  lng FLOAT64,
  description STRING,
  zone STRING,
  tags ARRAY<STRING>
);
```

---

## Example Queries

- `Tell me about animals near the Central Park Zoo`
- `What endangered species can I find there?`
- `Show me landmarks at the Central Park Zoo`
- `Tell me about arctic animals in the zoo`