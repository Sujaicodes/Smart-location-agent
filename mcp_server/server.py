"""
MCP Server for Smart Location Intelligence Agent.

Exposes location data via the Model Context Protocol (MCP).
Uses SQLite as the database backend (zero setup, no billing required).
In production, swap SQLite for BigQuery by setting USE_SQLITE=false.
"""

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(str(Path(__file__).parent.parent))
from shared.config import MOCK_DATA_PATH, GCP_PROJECT_ID, BIGQUERY_DATASET, BIGQUERY_TABLE

app = FastAPI(
    title="Location Intelligence MCP Server",
    description="MCP-compliant server for querying location/animal data",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

USE_SQLITE = os.environ.get("USE_SQLITE", "true").lower() == "true"
USE_MOCK = os.environ.get("USE_MOCK", "false").lower() == "true"

BASE_DIR = Path(__file__).parent.parent
SQLITE_DB_PATH = BASE_DIR / "data" / "locations.db"


# ─────────────────────────────────────────────
# MCP Protocol Models
# ─────────────────────────────────────────────

class MCPToolCall(BaseModel):
    tool_name: str
    parameters: dict[str, Any] = {}


class MCPToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Any
    error: str | None = None
    metadata: dict[str, Any] = {}


# ─────────────────────────────────────────────
# Data Layer
# ─────────────────────────────────────────────

def sqlite_rows_to_dicts(cursor) -> list[dict]:
    """Convert SQLite rows to list of dicts."""
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    result = []
    for row in rows:
        d = dict(zip(cols, row))
        # Convert tags string back to list
        if 'tags' in d and d['tags']:
            d['tags'] = d['tags'].split(',')
        else:
            d['tags'] = []
        result.append(d)
    return result


def get_sqlite_conn():
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def load_mock_data() -> list[dict]:
    with open(MOCK_DATA_PATH) as f:
        return json.load(f)


def query_bigquery(sql: str) -> list[dict]:
    from google.cloud import bigquery
    client = bigquery.Client(project=GCP_PROJECT_ID)
    query_job = client.query(sql)
    return [dict(row) for row in query_job.result()]


# ─────────────────────────────────────────────
# MCP Tools
# ─────────────────────────────────────────────

def tool_query_locations_by_name(params: dict) -> dict:
    location_name = params.get("location_name", "")
    limit = int(params.get("limit", 10))

    if not location_name:
        raise ValueError("'location_name' parameter is required.")

    if USE_MOCK:
        data = load_mock_data()
        results = [r for r in data if location_name.lower() in r.get("location_name", "").lower()][:limit]

    elif USE_SQLITE:
        conn = get_sqlite_conn()
        cur = conn.execute(
            "SELECT * FROM locations WHERE LOWER(location_name) LIKE ? LIMIT ?",
            (f"%{location_name.lower()}%", limit)
        )
        results = sqlite_rows_to_dicts(cur)
        conn.close()

    else:
        sql = f"""
            SELECT * FROM `{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}`
            WHERE LOWER(location_name) LIKE LOWER('%{location_name}%')
            LIMIT {limit}
        """
        results = query_bigquery(sql)

    return {"records": results, "count": len(results)}


def tool_query_by_type(params: dict) -> dict:
    record_type = params.get("type", "animal")
    location_name = params.get("location_name", "")

    if USE_MOCK:
        data = load_mock_data()
        results = [r for r in data if r.get("type") == record_type]
        if location_name:
            results = [r for r in results if location_name.lower() in r.get("location_name", "").lower()]

    elif USE_SQLITE:
        conn = get_sqlite_conn()
        if location_name:
            cur = conn.execute(
                "SELECT * FROM locations WHERE type=? AND LOWER(location_name) LIKE ?",
                (record_type, f"%{location_name.lower()}%")
            )
        else:
            cur = conn.execute("SELECT * FROM locations WHERE type=?", (record_type,))
        results = sqlite_rows_to_dicts(cur)
        conn.close()

    else:
        location_filter = f"AND LOWER(location_name) LIKE LOWER('%{location_name}%')" if location_name else ""
        sql = f"""
            SELECT * FROM `{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}`
            WHERE type = '{record_type}' {location_filter} LIMIT 20
        """
        results = query_bigquery(sql)

    return {"records": results, "count": len(results)}


def tool_query_by_tags(params: dict) -> dict:
    tags = params.get("tags", [])
    if not tags:
        raise ValueError("'tags' list is required.")

    if USE_MOCK:
        data = load_mock_data()
        results = [
            r for r in data
            if any(tag.lower() in [t.lower() for t in r.get("tags", [])] for tag in tags)
        ]

    elif USE_SQLITE:
        conn = get_sqlite_conn()
        conditions = " OR ".join(["LOWER(tags) LIKE ?" for _ in tags])
        values = [f"%{tag.lower()}%" for tag in tags]
        cur = conn.execute(f"SELECT * FROM locations WHERE {conditions}", values)
        results = sqlite_rows_to_dicts(cur)
        conn.close()

    else:
        tag_conditions = " OR ".join([f"LOWER(TO_JSON_STRING(tags)) LIKE '%{t.lower()}%'" for t in tags])
        sql = f"""
            SELECT * FROM `{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}`
            WHERE {tag_conditions} LIMIT 20
        """
        results = query_bigquery(sql)

    return {"records": results, "count": len(results)}


def tool_raw_sql(params: dict) -> dict:
    sql = params.get("sql", "")
    if not sql:
        raise ValueError("'sql' parameter is required.")

    if USE_SQLITE:
        conn = get_sqlite_conn()
        cur = conn.execute(sql)
        results = sqlite_rows_to_dicts(cur)
        conn.close()
        return {"records": results, "count": len(results)}

    if USE_MOCK:
        return {"error": "Raw SQL not available in mock mode."}

    results = query_bigquery(sql)
    return {"records": results, "count": len(results)}


# ─────────────────────────────────────────────
# Tool Registry
# ─────────────────────────────────────────────

TOOL_REGISTRY = {
    "query_locations_by_name": tool_query_locations_by_name,
    "query_by_type": tool_query_by_type,
    "query_by_tags": tool_query_by_tags,
    "raw_sql": tool_raw_sql,
}


# ─────────────────────────────────────────────
# MCP Endpoints
# ─────────────────────────────────────────────

@app.get("/health")
def health_check():
    mode = "mock" if USE_MOCK else ("sqlite" if USE_SQLITE else "bigquery")
    return {"status": "ok", "mode": mode, "db_path": str(SQLITE_DB_PATH) if USE_SQLITE else None}


@app.get("/tools")
def list_tools():
    return {
        "tools": [
            {"name": "query_locations_by_name", "description": "Search by location name", "parameters": {"location_name": "string (required)", "limit": "int (optional)"}},
            {"name": "query_by_type", "description": "Filter by type: animal or landmark", "parameters": {"type": "string", "location_name": "string (optional)"}},
            {"name": "query_by_tags", "description": "Find records matching tags", "parameters": {"tags": "list[string]"}},
            {"name": "raw_sql", "description": "Execute raw SQL", "parameters": {"sql": "string"}},
        ]
    }


@app.post("/invoke", response_model=MCPToolResult)
async def invoke_tool(call: MCPToolCall, request: Request):
    tool_fn = TOOL_REGISTRY.get(call.tool_name)
    if not tool_fn:
        raise HTTPException(status_code=404, detail=f"Tool '{call.tool_name}' not found.")
    try:
        result_data = tool_fn(call.parameters)
        mode = "mock" if USE_MOCK else ("sqlite" if USE_SQLITE else "bigquery")
        return MCPToolResult(tool_name=call.tool_name, success=True, data=result_data, metadata={"mode": mode})
    except ValueError as e:
        return MCPToolResult(tool_name=call.tool_name, success=False, data=None, error=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)