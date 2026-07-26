#!/usr/bin/env python3
"""
Create Region rayan1 Script
- Creates a 60x60 WorldGuard region named 'rayan1' for Rayan Saleh (NightmareDady).
- Coordinates: min (1196, 63, -133) to max (1255, 256, -74) which is centered at (1226, 63, -103).
- Registers it in player_regions_registry.json.
- Syncs the updated regions.yml to the Exaroton server and reloads WorldGuard.
- Supports --undo to roll back the region creation.
"""

import os
import sys
import json
import time
import subprocess
import yaml

PLUGINS_DIR = "/Users/hanansaleh/Downloads/plugins"
REGIONS_YML_PATH = os.path.join(PLUGINS_DIR, "WorldGuard", "worlds", "world", "regions.yml")
REGISTRY_JSON_PATH = os.path.join(PLUGINS_DIR, "player_regions_registry.json")

BACKUP_REGIONS_PATH = os.path.join(PLUGINS_DIR, "WorldGuard", "worlds", "world", "regions.yml.bak_create_rayan1")
BACKUP_REGISTRY_PATH = os.path.join(PLUGINS_DIR, "player_regions_registry.json.bak_create_rayan1")

SYNC_PY_PATH = os.path.join(PLUGINS_DIR, "sync.py")

# Load environment variables from .env
ENV_FILE = os.path.join(PLUGINS_DIR, ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()

HARDCODED_TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
HARDCODED_SERVER_ID = "cEuS61sZvNEFS3aB"

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or HARDCODED_TOKEN
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or HARDCODED_SERVER_ID

def send_exaroton_command(cmd):
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/command/"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"command": cmd})
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        if data.get("success"):
            print(f"✅ Console Executed: {cmd}")
            return True
        else:
            print(f"❌ Command Error: {data.get('error')} | Output: {res.stdout}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def sync_and_reload():
    push_cmd = ["python3", SYNC_PY_PATH, "push", "WorldGuard/worlds/world/regions.yml", "--force"]
    res = subprocess.run(push_cmd, capture_output=True, text=True)
    print(f"Sync Push Result: {res.stdout.strip()}")
    send_exaroton_command("wg reload")
    send_exaroton_command("rg reload")

def undo():
    print("Undoing rayan1 region creation...")
    if not os.path.exists(BACKUP_REGIONS_PATH) or not os.path.exists(BACKUP_REGISTRY_PATH):
        print("Error: Backup files not found. Cannot undo.")
        return False
    
    # Restore regions.yml
    with open(BACKUP_REGIONS_PATH, "r") as f:
        regions_content = f.read()
    with open(REGIONS_YML_PATH, "w") as f:
        f.write(regions_content)
    print("Restored regions.yml.")
    
    # Restore registry
    with open(BACKUP_REGISTRY_PATH, "r") as f:
        registry_content = f.read()
    with open(REGISTRY_JSON_PATH, "w") as f:
        f.write(registry_content)
    print("Restored player_regions_registry.json.")
    
    # Sync and reload
    sync_and_reload()
    
    # Clean up backups
    os.remove(BACKUP_REGIONS_PATH)
    os.remove(BACKUP_REGISTRY_PATH)
    print("Removed backup files.")
    return True

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--undo":
        undo()
        return

    # Check if backups already exist
    if os.path.exists(BACKUP_REGIONS_PATH) or os.path.exists(BACKUP_REGISTRY_PATH):
        if os.path.exists(BACKUP_REGIONS_PATH):
            os.remove(BACKUP_REGIONS_PATH)
        if os.path.exists(BACKUP_REGISTRY_PATH):
            os.remove(BACKUP_REGISTRY_PATH)

    # 1. Read files and create backups
    with open(REGIONS_YML_PATH, "r") as f:
        regions_raw = f.read()
    with open(BACKUP_REGIONS_PATH, "w") as f:
        f.write(regions_raw)
        
    with open(REGISTRY_JSON_PATH, "r") as f:
        registry_raw = f.read()
    with open(BACKUP_REGISTRY_PATH, "w") as f:
        f.write(registry_raw)

    # 2. Modify regions.yml using PyYAML
    regions_data = yaml.safe_load(regions_raw) or {}
    if "regions" not in regions_data:
        regions_data["regions"] = {}
        
    if "rayan1" in regions_data["regions"]:
        print("Error: Region 'rayan1' already exists in regions.yml!")
        return

    # Set coordinates and properties (60x60, centered at (1226, 63, -103))
    regions_data["regions"]["rayan1"] = {
        "type": "cuboid",
        "min": {"x": 1196, "y": 63, "z": -133},
        "max": {"x": 1255, "y": 256, "z": -74},
        "priority": 0,
        "flags": {
            "pvp": "allow"
        },
        "owners": {
            "unique-ids": ["d413c28e-64bb-32af-9661-3e901bc6e22b"]
        },
        "members": {}
    }

    # Write regions.yml
    with open(REGIONS_YML_PATH, "w") as f:
        yaml.dump(regions_data, f, default_flow_style=False)
    print("Updated regions.yml locally.")

    # 3. Modify player_regions_registry.json
    registry_data = json.loads(registry_raw)
    if "regions" not in registry_data:
        registry_data["regions"] = {}
        
    registry_data["regions"]["rayan1"] = {
        "player_name": "rayan saleh",
        "username": "NightmareDady",
        "min_corner": {"x": 1196, "y": 63, "z": -133},
        "max_corner": {"x": 1255, "y": 256, "z": -74},
        "dimensions": {
            "width_x": 60,
            "length_z": 60,
            "height_y": 194
        },
        "surface_area_sq_blocks": 3600,
        "size_category": "Big Plot",
        "raw_uuids": "d413c28e-64bb-32af-9661-3e901bc6e22b",
        "floor_y_level": 63
    }
    registry_data["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    # Write registry
    with open(REGISTRY_JSON_PATH, "w") as f:
        json.dump(registry_data, f, indent=4)
    print("Updated player_regions_registry.json locally.")

    # 4. Sync to server and reload
    sync_and_reload()
    print("Successfully created region 'rayan1'!")

if __name__ == "__main__":
    main()
