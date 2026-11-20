"""Seed script for Traveler AI Firestore database."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-84eb67ecd5b2"
COLLECTION_NAME = "destinations"

SAMPLE_DESTINATIONS = [
    {
        "id": "kyoto-fushimi-inari",
        "name": "Fushimi Inari Taisha",
        "city": "Kyoto",
        "country": "Japan",
        "category": "Culture & Shrine",
        "description": "Famous Shinto shrine renowned for its thousands of vibrant vermilion torii gates winding up Mount Inari.",
        "recommended_duration_hours": 3.0,
        "admission_fee_usd": 0.0,
        "best_time_of_day": "Early morning or sunset",
        "tags": ["culture", "photography", "hiking", "free"]
    },
    {
        "id": "paris-louvre-museum",
        "name": "Louvre Museum",
        "city": "Paris",
        "country": "France",
        "category": "Museum & Art",
        "description": "World's largest art museum and historic monument home to the Mona Lisa and Venus de Milo.",
        "recommended_duration_hours": 4.0,
        "admission_fee_usd": 24.0,
        "best_time_of_day": "Morning",
        "tags": ["art", "history", "indoor", "culture"]
    },
    {
        "id": "sf-golden-gate-bridge",
        "name": "Golden Gate Bridge",
        "city": "San Francisco",
        "country": "United States",
        "category": "Landmark & Sightseeing",
        "description": "Iconic suspension bridge spanning the Golden Gate strait between San Francisco and Marin County.",
        "recommended_duration_hours": 2.0,
        "admission_fee_usd": 0.0,
        "best_time_of_day": "Afternoon",
        "tags": ["sightseeing", "scenic", "walking", "photography"]
    },
    {
        "id": "rome-colosseum",
        "name": "Colosseum",
        "city": "Rome",
        "country": "Italy",
        "category": "Historic Landmark",
        "description": "Ancient amphitheater built under the Flavian emperors, symbol of imperial Roman architecture and gladiatorial combat.",
        "recommended_duration_hours": 2.5,
        "admission_fee_usd": 20.0,
        "best_time_of_day": "Early morning",
        "tags": ["history", "architecture", "unesco", "landmark"]
    },
    {
        "id": "banff-lake-louise",
        "name": "Lake Louise",
        "city": "Banff",
        "country": "Canada",
        "category": "Nature & Adventure",
        "description": "Glacial lake known for its turquoise waters, dramatic mountain backdrop, and scenic canoeing/hiking trails.",
        "recommended_duration_hours": 3.5,
        "admission_fee_usd": 15.0,
        "best_time_of_day": "Morning",
        "tags": ["nature", "hiking", "lake", "scenic", "outdoor"]
    }
]


def seed():
    print(f"Connecting to Firestore for project: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection(COLLECTION_NAME)

    for item in SAMPLE_DESTINATIONS:
        doc_id = item["id"]
        doc_ref = collection.document(doc_id)
        doc_ref.set(item)
        print(f"Seeded destination: {item['name']} ({doc_id})")

    print(f"\nSuccessfully seeded {len(SAMPLE_DESTINATIONS)} destinations into '{COLLECTION_NAME}' collection.")


if __name__ == "__main__":
    seed()
