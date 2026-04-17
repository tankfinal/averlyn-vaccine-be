"""
Migration script: reads data.json from the static site and inserts into Supabase.

Usage:
    python -m scripts.migrate_data

Requires SUPABASE_URL and SUPABASE_SERVICE_KEY in .env or environment.
"""

import json
import os
import sys

from dotenv import load_dotenv
from supabase import create_client

# Load .env from project root
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set.")
    sys.exit(1)

# Path to the original data.json
DATA_JSON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "averlyn-vaccine", "data.json"
)

# Allow overriding via env var or CLI arg
if len(sys.argv) > 1:
    DATA_JSON_PATH = sys.argv[1]


def main():
    # Read data.json
    data_path = os.path.abspath(DATA_JSON_PATH)
    print(f"Reading data from: {data_path}")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # 1. Insert baby record
    baby = data["baby"]
    baby_row = {
        "id": 1,
        "name": baby["name"],
        "birth_date": baby["birthDate"],
    }
    print(f"Inserting baby: {baby_row['name']}")
    supabase.table("baby").upsert(baby_row, on_conflict="id").execute()

    # 2. Insert vaccines
    vaccines = data["vaccines"]
    rows = []
    for idx, v in enumerate(vaccines):
        row = {
            "id": v["id"],
            "name": v["name"],
            "name_en": v.get("nameEn", ""),
            "subtitle": v.get("subtitle"),
            "type": v["type"],
            "done": v.get("done", False),
            "done_date": v.get("doneDate"),
            "scheduled_date": v.get("scheduledDate"),
            "price": v.get("price"),
            "description": v["description"],
            "side_effects": v.get("sideEffects"),
            "notes": v.get("notes"),
            "display_order": idx + 1,
        }
        rows.append(row)

    print(f"Inserting {len(rows)} vaccines...")
    supabase.table("vaccines").upsert(rows, on_conflict="id").execute()

    print("Migration complete!")
    print(f"  - Baby: {baby_row['name']} (born {baby_row['birth_date']})")
    print(f"  - Vaccines: {len(rows)} records")


if __name__ == "__main__":
    main()
