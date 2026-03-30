"""
Agent API Server with Web UI.

Wraps the SmartLocationAgent in a FastAPI web server,
serves the HTML frontend, and exposes a /query endpoint.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

from agent.agent import SmartLocationAgent

app = FastAPI(title="Smart Location Intelligence Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = SmartLocationAgent()

BASE_DIR = Path(__file__).parent
TEMPLATE_PATH = BASE_DIR / "templates" / "index.html"


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    response: str
    success: bool
    error: str | None = None


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return TEMPLATE_PATH.read_text()


@app.get("/health")
def health():
    return {"status": "ok", "service": "agent"}


@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    try:
        response = agent.run(request.query)
        return QueryResponse(query=request.query, response=response, success=True)
    except Exception as e:
        return QueryResponse(query=request.query, response="", success=False, error=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("agent_api:app", host="0.0.0.0", port=port, reload=False)