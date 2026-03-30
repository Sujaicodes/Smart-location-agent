```
███████╗██╗     ██╗ █████╗
██╔════╝██║     ██║██╔══██╗
███████╗██║     ██║███████║
╚════██║██║     ██║██╔══██║
███████║███████╗██║██║  ██║
╚══════╝╚══════╝╚═╝╚═╝  ╚═╝
Smart Location Intelligence Agent
```

<div align="center">

[![Live Demo](https://img.shields.io/badge/⬡_Live_Demo-Railway-00ff88?style=for-the-badge&logoColor=white)](https://luminous-courage-production-7650.up.railway.app)
[![MCP Server](https://img.shields.io/badge/◎_MCP_Server-Online-00b4ff?style=for-the-badge)](https://smart-location-agent-v2-production.up.railway.app/health)
[![Python](https://img.shields.io/badge/Python-3.11-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285f4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Railway](https://img.shields.io/badge/Deployed_on-Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app)

**An AI-powered tour guide that bridges raw spatial data and natural conversational reasoning — built on the Model Context Protocol, powered by Gemini 2.5 Flash, deployed live.**

[🚀 Live Demo](https://luminous-courage-production-7650.up.railway.app) · [⬡ MCP Server](https://smart-location-agent-v2-production.up.railway.app/tools) · [📖 How It Works](#how-it-works)

</div>

---

## ⬡ What is SLIA?

SLIA is a full-stack AI agent system that lets anyone ask natural language questions about animals and exhibits at 7 of the world's best zoos — and receive rich, conversational tour-guide narratives in return.

But what makes it interesting isn't *what* it does. It's **how** it does it.

Instead of giving the AI direct database access, SLIA implements a strict **MCP (Model Context Protocol) client-server architecture** — a secure, standardized way for AI agents to talk to external tools. The agent never touches the database directly. It calls the MCP Server, which executes SQL and returns structured data. Clean. Isolated. Production-grade.

```
7 Zoos  ·  35 Animals  ·  2 Microservices  ·  5-step Pipeline  ·  100% Free Tools
```

---

## 🗺️ Live Features

| Feature | Description |
|---|---|
| **⬡ Ask Agent** | Natural language queries → full tour-guide narrative via Gemini 2.5 Flash |
| **◎ Map View** | Interactive dark world map with clickable zoo markers (Leaflet.js) |
| **⊞ Animal Search** | Browse, filter, and search all 35 animals across 7 zoos |
| **↗ Share Responses** | Copy or share any response via native Web Share API |
| **⊙ Real Geocoding** | Live coordinates from OpenStreetMap Nominatim — no API key needed |
| **◑ Live Wikipedia** | Real-time encyclopedic enrichment fetched fresh on every query |

---

## 🔌 How It Works

```
User Query
    │
    ▼
┌─────────────────────────────────┐
│     ADK Agent  (Gemini 2.5)     │  ← agent/agent.py
│                                 │
│  1. parse_intent()              │  Extract zoo, type, tags from query
│  2. MCPClient.invoke() ────────►│──► MCP Server → SQLite
│  3. geocode_location() ────────►│──► OpenStreetMap Nominatim
│  4. fetch_wikipedia()  ────────►│──► Wikipedia REST API
│  5. Gemini.synthesize()────────►│──► Gemini 2.5 Flash
└─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│    MCP Server  (Railway)         │
│    FastAPI · server.py           │
│                                  │
│  MCP Tools:                      │
│  · query_locations_by_name       │
│  · query_by_type                 │
│  · query_by_tags                 │
│  · raw_sql                       │
│            │                     │
│            ▼                     │
│   SQLite  locations.db           │
│   7 zoos · 35 animals            │
└──────────────────────────────────┘
```

### Step-by-step

1. **Intent Parsing** — Gemini reads your query and extracts the zoo name, record type (animal/landmark), and theme tags (endangered, arctic, etc.)
2. **MCP Call → SQLite** — The agent sends a secure HTTP request to the isolated MCP Server on Railway. The server runs SQL and returns structured animal records.
3. **Geocoding** — OpenStreetMap Nominatim converts the zoo name to real GPS coordinates and a formatted address. Free, no API key.
4. **Wikipedia Enrichment** — Live Wikipedia summaries are fetched for the top animals and injected into the synthesis prompt.
5. **Gemini Synthesis** — All data is assembled into a rich context payload. Gemini 2.5 Flash writes a vivid, conversational tour-guide narrative.

---

## 🗄️ Database

Currently covers **7 world-class zoos** with **35 entries**:

| Zoo | Location | Entries |
|---|---|---|
| Central Park Zoo | New York, USA | 5 |
| San Diego Zoo | California, USA | 5 |
| London Zoo | London, UK | 5 |
| Singapore Zoo | Singapore | 5 |
| Toronto Zoo | Ontario, Canada | 5 |
| Smithsonian National Zoo | Washington DC, USA | 5 |
| Melbourne Zoo | Melbourne, Australia | 5 |

---

## 🛠️ Tech Stack

| Layer | Technology | Role |
|---|---|---|
| **AI Core** | Google Gemini 2.5 Flash | Intent parsing + narrative synthesis |
| **Protocol** | Model Context Protocol (MCP) | Secure agent-to-tool communication |
| **Backend** | Python 3.11 + FastAPI | Agent API + MCP Server |
| **Database** | SQLite | Location + animal data store |
| **Geocoding** | OpenStreetMap Nominatim | Free real-time geocoding |
| **Enrichment** | Wikipedia REST API | Live factual summaries |
| **Frontend** | HTML + CSS + Leaflet.js | Web UI + interactive map |
| **Deployment** | Railway | Serverless cloud hosting |
| **Containers** | Docker | Service containerization |
| **Validation** | Pydantic | MCP request/response models |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- A [Gemini API key](https://aistudio.google.com/apikey) (free)

### Run Locally

**Terminal 1 — Start MCP Server:**
```powershell
pip install -r mcp_server/requirements.txt
$env:USE_SQLITE="true"; $env:USE_MOCK="false"
python mcp_server/server.py
# → http://localhost:8080
```

**Terminal 2 — Run Agent CLI:**
```powershell
pip install -r requirements.txt
$env:GEMINI_API_KEY="your-key-here"
$env:GEMINI_MODEL="gemini-2.5-flash"
$env:MCP_SERVER_URL="http://localhost:8080"
python main.py
```

**Or run the Web UI:**
```powershell
uvicorn agent_api:app --host 0.0.0.0 --port 8000
# → Open http://localhost:8000
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | — | Gemini API key from Google AI Studio |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `MCP_SERVER_URL` | `http://localhost:8080` | MCP Server URL |
| `USE_SQLITE` | `true` | Use SQLite database |
| `USE_MOCK` | `false` | Use mock JSON data |
| `USE_IAM_AUTH` | `false` | GCP IAM auth for Cloud Run |

---

## 📁 Project Structure

```
smart-location-agent/
├── main.py                    # CLI entrypoint (interactive REPL)
├── agent_api.py               # FastAPI web server + /query endpoint
├── requirements.txt
├── Dockerfile                 # Agent container
├── Procfile                   # Railway start command
├── railway.toml               # Railway deployment config
│
├── shared/
│   └── config.py              # All env vars + paths
│
├── data/
│   ├── mock_locations.json    # Source data (7 zoos, 35 animals)
│   └── locations.db           # SQLite database
│
├── mcp_server/
│   ├── server.py              # FastAPI MCP Server (4 tools)
│   ├── requirements.txt
│   └── Dockerfile
│
├── agent/
│   ├── agent.py               # Core orchestration logic
│   ├── mcp_client.py          # HTTP client for MCP Server
│   └── external_tools.py      # OpenStreetMap + Wikipedia tools
│
├── templates/
│   └── index.html             # Web UI (Ask + Map + Search tabs)
│
└── scripts/
    ├── deploy.sh              # Cloud Run deployment
    └── iam_setup.sh           # GCP IAM setup
```

---

## 🔭 Future Goals

### 🟢 Near Term (1–2 weeks)
- **BigQuery Backend** — Swap SQLite for Google BigQuery for petabyte-scale datasets
- **Chat History** — Persist conversation context across sessions
- **50+ Zoos** — Expand database to cover every continent

### 🔵 Mid Term (1–2 months)
- **Voice Input & Output** — Web Speech API for true audio tour guide experience
- **Google Cloud Run** — Migrate to Cloud Run with full IAM service-to-service auth
- **Multi-modal Animal Cards** — Real photos, IUCN status badges, range maps

### 🟠 Long Term (3–6 months)
- **Custom MCP Tool Registry** — Let any zoo plug in their own data source
- **Mobile App** — GPS-aware iOS/Android app for in-zoo navigation
- **Multi-agent System** — Conservation Agent, Route Planner, Kids Mode — all coordinated via MCP

---

## 🏗️ Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and init
railway login
railway init

# Deploy MCP Server
railway service
railway up

# Set env vars on agent service
railway variables set GEMINI_API_KEY="..." GEMINI_MODEL="gemini-2.5-flash" MCP_SERVER_URL="https://your-mcp-url.railway.app"
```

---

## 📄 License

MIT License — free to use, modify, and deploy.

---

<div align="center">

Built with ❤️ using **MCP · Gemini · FastAPI · Railway**

[⬡ Live Demo](https://luminous-courage-production-7650.up.railway.app) · [◎ MCP Health](https://smart-location-agent-v2-production.up.railway.app/health) · [⊞ MCP Tools](https://smart-location-agent-v2-production.up.railway.app/tools)

</div>
