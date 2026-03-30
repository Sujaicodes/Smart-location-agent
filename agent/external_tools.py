"""
External enrichment tools used by the ADK Agent.

- Wikipedia: fetches a plain-text summary for any topic
- Nominatim (OpenStreetMap): free geocoding, no API key required
"""

import urllib.parse

import requests


# ─────────────────────────────────────────────
# Wikipedia Tool
# ─────────────────────────────────────────────

def fetch_wikipedia_summary(topic: str, sentences: int = 3) -> dict:
    encoded = urllib.parse.quote(topic)
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "SmartLocationAgent/1.0"})
        if resp.status_code == 404:
            return _wikipedia_search_fallback(topic)
        resp.raise_for_status()
        data = resp.json()
        return {
            "title": data.get("title"),
            "summary": data.get("extract", "")[:800],
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }
    except Exception as e:
        return {"error": str(e), "topic": topic}


def _wikipedia_search_fallback(topic: str) -> dict:
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {"action": "opensearch", "search": topic, "limit": 1, "format": "json"}
    try:
        resp = requests.get(search_url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if data[1]:
            return fetch_wikipedia_summary(data[1][0])
        return {"error": f"No Wikipedia article found for '{topic}'"}
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
# Nominatim (OpenStreetMap) Geocoding Tool
# Free, no API key required.
# ─────────────────────────────────────────────

def geocode_location(location_name: str) -> dict:
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location_name, "format": "json", "limit": 1, "addressdetails": 1}
    headers = {"User-Agent": "SmartLocationAgent/1.0 (educational project)"}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        if not data:
            return {"error": f"No results found for '{location_name}'"}

        result = data[0]
        address_parts = result.get("address", {})

        return {
            "formatted_address": result.get("display_name", location_name),
            "lat": float(result["lat"]),
            "lng": float(result["lon"]),
            "city": address_parts.get("city") or address_parts.get("town", ""),
            "country": address_parts.get("country", ""),
            "source": "OpenStreetMap Nominatim",
        }
    except Exception as e:
        return {"error": str(e)}