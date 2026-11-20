"""Google Maps Geocoding and Places (New) function tools for Traveler AI."""

import json
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


def _get_api_key() -> str:
    """Read Google Maps API key from environment."""
    key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    return key.strip()


def geocode_address(address: str) -> Dict[str, Any]:
    """Converts a street address, landmark, or city name into latitude/longitude coordinates.

    Args:
        address: The address or place to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'Eiffel Tower, Paris').

    Returns:
        A dictionary with formatted address, latitude, and longitude.
    """
    key = _get_api_key()
    if not key or key == "PASTE_KEY_HERE":
        return {"error": "GOOGLE_MAPS_API_KEY is not configured in .env."}

    encoded = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded}&key={key}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TravelerAI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        status = data.get("status")
        if status != "OK":
            return {"error": f"Geocoding API error: {status}", "details": data.get("error_message")}

        result = data["results"][0]
        location = result["geometry"]["location"]
        return {
            "name": address,
            "address": result.get("formatted_address"),
            "location": {
                "latitude": location["lat"],
                "longitude": location["lng"],
            },
            "place_id": result.get("place_id"),
        }
    except Exception as e:
        return {"error": f"Failed to call Geocoding API: {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "tourist_attraction",
    radius_meters: float = 1500.0,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """Finds nearby places of a given type around coordinates using Places API (New).

    Args:
        latitude: Latitude of the center point (e.g. 48.8584).
        longitude: Longitude of the center point (e.g. 2.2945).
        place_type: Place type to search for (e.g. 'restaurant', 'cafe', 'museum', 'tourist_attraction', 'lodging', 'park').
        radius_meters: Search radius in meters, up to 50000.0 (default 1500.0).
        max_results: Maximum results to return (1 to 20, default 5).

    Returns:
        A list of nearby places with name, address, location, and rating.
    """
    key = _get_api_key()
    if not key or key == "PASTE_KEY_HERE":
        return [{"error": "GOOGLE_MAPS_API_KEY is not configured in .env."}]

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating,places.types",
    }

    payload = {
        "includedTypes": [place_type],
        "maxResultCount": min(max(1, max_results), 20),
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": float(radius_meters),
            }
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        places = data.get("places", [])
        if not places:
            return []

        results = []
        for p in places:
            display_name = p.get("displayName", {}).get("text", "Unknown")
            results.append({
                "name": display_name,
                "address": p.get("formattedAddress"),
                "location": {
                    "latitude": p.get("location", {}).get("latitude"),
                    "longitude": p.get("location", {}).get("longitude"),
                },
                "rating": p.get("rating"),
            })
        return results
    except Exception as e:
        return [{"error": f"Failed to call Places API (New): {str(e)}"}]
