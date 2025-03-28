import json
import os

CACHE_FILE = "offline_shipments_cache.json"

def save_shipment_to_cache(shipment):
    cache = load_cached_shipments()
    cache.append(shipment)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def load_cached_shipments():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return []

def sync_cached_shipments(session):
    cache = load_cached_shipments()
    for s in cache:
        # Create a new Shipment record using the data from s
        new_ship = Shipment(
            shipment_id=s["ID"],
            status=s["Status"],
            checked=s["Checked"],
            employee_id=s["employee_id"],
            imported=s.get("imported", True),
            inspected_date=s.get("inspected_date")
        )
        session.add(new_ship)
    session.commit()
    # Clear cache after syncing
    with open(CACHE_FILE, "w") as f:
        json.dump([], f)
