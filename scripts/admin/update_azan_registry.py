import json
import os

registry_path = "player_regions_registry.json"

if os.path.exists(registry_path):
    with open(registry_path, "r") as f:
        registry = json.load(f)
else:
    registry = {"regions": {}}

azan_region = {
    "owner_uuid": "e458e0be-6d80-32b0-8f9f-52467b7f1e58", # Assumed based on typical Bedrock UUIDs or can be left generic
    "owner_name": "azansalehhh",
    "coordinates": {
        "min": {"x": 1241, "y": 0, "z": -219},
        "max": {"x": 1255, "y": 255, "z": -191}
    },
    "dimensions": {
        "width_x": 15,
        "length_z": 29
    },
    "size_category": "Normal Plot",
    "floor_markings": "2-color concrete floor (Cyan North, Red South). House built ONLY on South half (Red part). North half is an open Cyan yard. Basic interiors included."
}

registry["regions"]["azansalehhh"] = azan_region

with open(registry_path, "w") as f:
    json.dump(registry, f, indent=4)

print("Updated player_regions_registry.json")
