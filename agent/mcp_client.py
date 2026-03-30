"""
MCP Client for the ADK Agent.

Handles all communication from the agent to the MCP Server deployed on Cloud Run.
In production, attaches an IAM ID Token for service-to-service authentication.
"""

import os
from typing import Any

import requests

from shared.config import MCP_SERVER_URL


class MCPClient:
    """
    Lightweight MCP client that the ADK Agent uses to call the MCP Server.

    In production (Cloud Run), it fetches an OIDC ID token from the metadata
    server and attaches it as a Bearer token for IAM authentication.
    """

    def __init__(self, server_url: str = MCP_SERVER_URL):
        self.server_url = server_url.rstrip("/")
        self.use_iam_auth = os.environ.get("USE_IAM_AUTH", "false").lower() == "true"

    def _get_id_token(self) -> str:
        """
        Fetch an OIDC ID token from the GCE metadata server.
        Only works when running inside a GCP environment (Cloud Run, GCE, etc).
        """
        audience = self.server_url
        metadata_url = (
            f"http://metadata.internal/computeMetadata/v1/instance/service-accounts"
            f"/default/identity?audience={audience}"
        )
        resp = requests.get(metadata_url, headers={"Metadata-Flavor": "Google"}, timeout=5)
        resp.raise_for_status()
        return resp.text.strip()

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.use_iam_auth:
            token = self._get_id_token()
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def list_tools(self) -> list[dict]:
        """Fetch available tools from the MCP Server."""
        resp = requests.get(f"{self.server_url}/tools", headers=self._headers(), timeout=10)
        resp.raise_for_status()
        return resp.json().get("tools", [])

    def invoke(self, tool_name: str, parameters: dict[str, Any] = {}) -> dict:
        """
        Invoke a tool on the MCP Server.

        Returns the full MCPToolResult dict, including:
            - success (bool)
            - data (any)
            - error (str | None)
            - metadata (dict)
        """
        payload = {"tool_name": tool_name, "parameters": parameters}
        resp = requests.post(
            f"{self.server_url}/invoke",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def health(self) -> dict:
        resp = requests.get(f"{self.server_url}/health", headers=self._headers(), timeout=5)
        resp.raise_for_status()
        return resp.json()
