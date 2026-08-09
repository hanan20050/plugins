#!/usr/bin/env python3
"""
Sync live WorldGuard regions from `regions.yml` into `player_regions_registry.json`
and maintain persistent tracking of player region floor markings and dimensions.
"""

import os
import json
import re
import datetime

REGIONS_YML = "WorldGuard/worlds/world/regions.yml"
REGISTRY_FILE = "player_regions_registry.json"

def sync_registry():
    if not os.path.exists(REGIONS_YML):
        print(f"[ERROR] {REGIONS_YML} not found.")
        return

    with open(REGIONS_YML, "r") as f:
        text = f.read()

    existing_data = {}
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            try:
                existing_data = json.load(f)
            except Exception:
                existing_data = {}

    existing_regions = existing_data.get("regions", {})

    blocks = re.split(r'\n    ([a-zA-Z0-9_\-\.]+):\n', text)
    updated_regions = {}

    if len(blocks) > 1:
        for i in range(1, len(blocks), 2):
            rname = blocks[i]
            rcontent = blocks[i+1]

            min_m = re.search(r'min:\s*\{x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)\}', rcontent)
            max_m = re.search(r'max:\s*\{x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)\}', rcontent)

            if min_m and max_m:
                min_x, min_y, min_z = int(min_m.group(1)), int(min_m.group(2)), int(min_m.group(3))
                max_x, max_y, max_z = int(max_m.group(1)), int(max_m.group(2)), int(max_m.group(3))

                width = (max_x - min_x) + 1
                length = (max_z - min_z) + 1
                height = (max_y - min_y) + 1

                max_dim = max(width, length)
                if max_dim < 15:
                    cat = "Starter / Base Plot"
                elif max_dim <= 25:
                    cat = "Small Plot"
                elif max_dim <= 50:
                    cat = "Normal Plot"
                else:
                    cat = "Big Plot"

                entry = existing_regions.get(rname, {})
                entry["min_corner"] = {"x": min_x, "y": min_y, "z": min_z}
                entry["max_corner"] = {"x": max_x, "y": max_y, "z": max_z}
                entry["dimensions"] = {"width_x": width, "length_z": length, "height_y": height}
                entry["surface_area_sq_blocks"] = width * length
                entry["size_category"] = cat

                # Extract UUIDs if available
                uuids = re.findall(r'unique-ids:\s*\[(.*?)\]', rcontent)
                if uuids:
                    entry["raw_uuids"] = uuids[0]

                updated_regions[rname] = entry

    output = {
        "last_updated": datetime.datetime.now().isoformat(),
        "regions": updated_regions
    }

    with open(REGISTRY_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Successfully updated {REGISTRY_FILE} with {len(updated_regions)} server regions.")

if __name__ == "__main__":
    sync_registry()
