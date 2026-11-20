"""Firestore client and tools for Traveler AI."""

from typing import Any, Dict, List, Optional
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-84eb67ecd5b2"
COLLECTION_NAME = "destinations"

_db = None


def get_db() -> firestore.Client:
    """Get or initialize Firestore client with hardcoded project ID."""
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def list_destinations(city: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """List travel destinations from Firestore catalog, optionally filtering by city or category.

    Args:
        city: Optional city name to filter by (e.g. 'Kyoto', 'Paris', 'San Francisco', 'Rome').
        category: Optional category to filter by (e.g. 'Museum', 'Culture', 'Nature').

    Returns:
        A list of destination dictionaries matching the criteria.
    """
    db = get_db()
    docs = db.collection(COLLECTION_NAME).stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        if city and city.lower() not in data.get("city", "").lower():
            continue
        if category and category.lower() not in data.get("category", "").lower():
            continue
        results.append(data)
    return results


def get_destination_details(destination_id: str) -> Dict[str, Any]:
    """Retrieve detailed information for a specific destination by its ID or slug.

    Args:
        destination_id: The document ID of the destination (e.g. 'kyoto-fushimi-inari', 'sf-golden-gate-bridge').

    Returns:
        The destination details dictionary, or an error message if not found.
    """
    db = get_db()
    doc_ref = db.collection(COLLECTION_NAME).document(destination_id)
    doc = doc_ref.get()
    if not doc.exists:
        # Also try searching by exact name or case-insensitive match
        for d in db.collection(COLLECTION_NAME).stream():
            data = d.to_dict()
            if (
                data.get("name", "").lower() == destination_id.lower()
                or data.get("id", "").lower() == destination_id.lower()
            ):
                return data
        return {"error": f"Destination '{destination_id}' not found."}
    return doc.to_dict()


def add_destination(
    name: str,
    city: str,
    country: str,
    category: str,
    description: str,
    recommended_duration_hours: float,
    admission_fee_usd: float = 0.0,
    best_time_of_day: str = "Morning",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Add a new destination or attraction to the catalog in Firestore.

    Args:
        name: Name of the attraction or destination.
        city: City where it is located.
        country: Country where it is located.
        category: Category (e.g., 'Historic Landmark', 'Nature & Adventure').
        description: A short overview of what to see or do there.
        recommended_duration_hours: How long visitors typically spend there (e.g., 2.5).
        admission_fee_usd: Admission cost in USD (0.0 if free).
        best_time_of_day: Recommended time to visit (e.g., 'Morning', 'Sunset').
        tags: List of descriptive keyword tags (e.g., ['history', 'photography']).

    Returns:
        A dictionary confirming the newly created destination with its ID.
    """
    db = get_db()
    doc_id = f"{city.lower().replace(' ', '-')}-{name.lower().replace(' ', '-')[:25]}"
    doc_ref = db.collection(COLLECTION_NAME).document(doc_id)

    item_data = {
        "id": doc_id,
        "name": name,
        "city": city,
        "country": country,
        "category": category,
        "description": description,
        "recommended_duration_hours": recommended_duration_hours,
        "admission_fee_usd": admission_fee_usd,
        "best_time_of_day": best_time_of_day,
        "tags": tags or [],
    }
    doc_ref.set(item_data)
    return {"status": "success", "message": f"Added destination '{name}'", "destination": item_data}
