"""
Smart Location Intelligence Agent.

Orchestrates:
  1. MCP Client  → BigQuery (location / animal data)
  2. Google Maps → geocoding
  3. Wikipedia   → factual enrichment
  4. Gemini      → narrative synthesis

This is the "brain" of the system. It decides which tools to call,
collects structured data from all sources, and asks Gemini to produce
a conversational tour-guide response.
"""

import json
import os
import re

import google.generativeai as genai  # type: ignore

from shared.config import GEMINI_MODEL, AGENT_NAME, AGENT_DESCRIPTION
from agent.mcp_client import MCPClient
from agent.external_tools import fetch_wikipedia_summary, geocode_location


# ─────────────────────────────────────────────
# Gemini Setup
# ─────────────────────────────────────────────

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# ─────────────────────────────────────────────
# Agent System Prompt
# ─────────────────────────────────────────────

SYSTEM_PROMPT = f"""
You are {AGENT_NAME}, {AGENT_DESCRIPTION}.

You have already retrieved structured data from multiple sources and it will be
provided to you as JSON. Your job is to synthesize this into a rich, engaging,
conversational tour-guide narrative.

Guidelines:
- Speak as a knowledgeable and enthusiastic local guide.
- Naturally weave in facts about animals, their habitats, and conservation status.
- Reference the geographic location and address from the map data.
- Incorporate historical or encyclopedic context from Wikipedia snippets.
- Do NOT mention the internal tools, APIs, or databases used.
- Keep the response friendly, vivid, and informative — 3 to 5 paragraphs.
"""


# ─────────────────────────────────────────────
# Intent Parser
# ─────────────────────────────────────────────

def parse_intent(user_query: str) -> dict:
    """
    Lightweight intent parsing to decide which MCP tools to call.

    Returns a dict like:
        {
            "location_name": "Central Park Zoo",
            "record_type": "animal",      # or "landmark" or None
            "tags": ["endangered"],        # extracted keywords
        }
    """
    query_lower = user_query.lower()

    # Detect record type
    record_type = None
    if any(w in query_lower for w in ["animal", "animals", "species", "wildlife", "creature"]):
        record_type = "animal"
    elif any(w in query_lower for w in ["landmark", "exhibit", "zone", "building"]):
        record_type = "landmark"

    # Detect tags/themes
    tag_keywords = {
        "endangered": ["endangered", "threatened", "rare"],
        "arctic": ["arctic", "polar", "cold"],
        "big cat": ["cat", "leopard", "tiger", "lion", "jaguar"],
        "bird": ["bird", "penguin", "parrot", "eagle"],
        "marine": ["marine", "ocean", "sea", "aquatic", "water"],
    }
    detected_tags = [
        tag
        for tag, words in tag_keywords.items()
        if any(w in query_lower for w in words)
    ]

    # Detect location name (simple heuristic: look for "at/near/in/about the X Zoo/Park/etc")
    location_name = "Central Park Zoo"  # Default for demo
    location_patterns = [
        r"(?:at|near|in|about|around)\s+(?:the\s+)?([A-Z][A-Za-z\s]+(?:Zoo|Park|Garden|Aquarium|Museum))",
        r"([A-Z][A-Za-z\s]+(?:Zoo|Park|Garden|Aquarium|Museum))",
    ]
    for pattern in location_patterns:
        match = re.search(pattern, user_query)
        if match:
            location_name = match.group(1).strip()
            break

    return {
        "location_name": location_name,
        "record_type": record_type,
        "tags": detected_tags,
    }


# ─────────────────────────────────────────────
# Core Agent Logic
# ─────────────────────────────────────────────

class SmartLocationAgent:
    def __init__(self):
        self.mcp = MCPClient()
        self.model = genai.GenerativeModel(GEMINI_MODEL) if GEMINI_API_KEY else None

    # ── Step 1: Retrieve from BigQuery via MCP ──────────────────────────────

    def _fetch_from_mcp(self, intent: dict) -> list[dict]:
        """Call the appropriate MCP tool based on parsed intent."""
        print(f"[Agent] MCP call → intent={intent}")

        location_name = intent["location_name"]
        record_type = intent["record_type"]
        tags = intent["tags"]

        # Prefer tag-based search if tags detected + type is animal
        if tags and record_type == "animal":
            result = self.mcp.invoke("query_by_tags", {"tags": tags})
        elif record_type:
            result = self.mcp.invoke(
                "query_by_type",
                {"type": record_type, "location_name": location_name},
            )
        else:
            result = self.mcp.invoke(
                "query_locations_by_name",
                {"location_name": location_name},
            )

        if not result.get("success"):
            print(f"[Agent] MCP error: {result.get('error')}")
            return []

        return result.get("data", {}).get("records", [])

    # ── Step 2: Enrich with Maps + Wikipedia ───────────────────────────────

    def _enrich(self, records: list[dict], location_name: str) -> dict:
        """Geocode the location and fetch Wikipedia summaries for key entities."""
        print(f"[Agent] Geocoding '{location_name}'...")
        geo = geocode_location(location_name)

        wiki_summaries = {}
        # Fetch Wikipedia for top 2 animals/landmarks to avoid rate limits
        for record in records[:2]:
            name = record.get("name", "")
            print(f"[Agent] Wikipedia → '{name}'")
            wiki_summaries[name] = fetch_wikipedia_summary(name)

        # Also fetch for the location itself
        print(f"[Agent] Wikipedia → '{location_name}'")
        wiki_summaries[location_name] = fetch_wikipedia_summary(location_name)

        return {"geo": geo, "wiki": wiki_summaries}

    # ── Step 3: Synthesize with Gemini ──────────────────────────────────────

    def _synthesize(self, user_query: str, records: list[dict], enrichment: dict) -> str:
        """Build the final narrative using Gemini."""

        context_payload = {
            "user_query": user_query,
            "location_data_from_bigquery": records,
            "geocoding_result": enrichment["geo"],
            "wikipedia_summaries": enrichment["wiki"],
        }

        prompt = (
            f"Here is the retrieved data in JSON format:\n\n"
            f"```json\n{json.dumps(context_payload, indent=2)}\n```\n\n"
            f"User asked: \"{user_query}\"\n\n"
            f"Please craft your tour-guide response now."
        )

        if self.model:
            response = self.model.generate_content(
                [{"role": "user", "parts": [SYSTEM_PROMPT + "\n\n" + prompt]}]
            )
            return response.text
        else:
            # Fallback: template response if no Gemini key
            return self._template_response(user_query, records, enrichment)

    def _template_response(self, query: str, records: list[dict], enrichment: dict) -> str:
        """Fallback narrative builder when Gemini is not configured."""
        geo = enrichment.get("geo", {})
        wiki = enrichment.get("wiki", {})

        lines = [
            f"Welcome to your tour of **{geo.get('formatted_address', 'the location')}**!",
            "",
        ]

        if records:
            lines.append(f"I found **{len(records)} entries** matching your query:\n")
            for r in records:
                name = r.get("name", "Unknown")
                desc = r.get("description", "")
                zone = r.get("zone", "")
                w = wiki.get(name, {})
                wiki_text = w.get("summary", "")[:200] if "summary" in w else ""

                lines.append(f"### {name}")
                if zone:
                    lines.append(f"📍 *{zone}*")
                lines.append(desc)
                if wiki_text:
                    lines.append(f"> {wiki_text}")
                lines.append("")
        else:
            lines.append("No specific records were found, but this is a wonderful location!")

        lines.append(
            f"📌 Coordinates: {geo.get('lat')}, {geo.get('lng')}"
        )
        return "\n".join(lines)

    # ── Main Entry Point ────────────────────────────────────────────────────

    def run(self, user_query: str) -> str:
        """
        Full agent pipeline:
          parse intent → MCP query → enrich → synthesize → return narrative
        """
        print(f"\n[Agent] Query: {user_query}")

        # 1. Parse intent
        intent = parse_intent(user_query)
        print(f"[Agent] Parsed intent: {intent}")

        # 2. Fetch from BigQuery via MCP
        records = self._fetch_from_mcp(intent)
        print(f"[Agent] Records retrieved: {len(records)}")

        # 3. Enrich with Maps + Wikipedia
        enrichment = self._enrich(records, intent["location_name"])

        # 4. Synthesize with Gemini (or fallback template)
        narrative = self._synthesize(user_query, records, enrichment)

        return narrative
