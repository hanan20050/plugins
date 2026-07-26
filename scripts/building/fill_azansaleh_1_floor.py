#!/usr/bin/env python3
"""
Fill Floor for azansaleh_1 Script
- Fills the base floor of Azan Saleh's new region 'azansaleh_1' (Y=63) with Dirt.
- Bounds: X: 1040..1084, Z: -174..-130, Y: 63.
- Supports dry-run and undo (--undo reverts Y=63 back to air and clears dropped items).
"""

import os
import sys
import json
import subprocess
import argparse

PLUGINS_DIR = "/Users/hanansaleh/Downloads/plugins"
REGISTRY_JSON_PATH = os.path.join(PLUGINS_DIR, "player_regions_registry.json")

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

MIN_X, MAX_X = 1040, 1084
MIN_Z, MAX_Z = -174, -130
FLOOR_Y = 63

def send_exaroton_command(cmd, dry_run=False):
    if dry_run:
        print(f"[DRY-RUN] Console Command: {cmd}")
        return True

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
        if not data.get("success", False):
            print(f"[ERROR] Exaroton Command Failed: {data.get('error')}")
            return False
        return True
    except Exception as e:
        print(f"[ERROR] Failed to parse API response: {res.stdout}")
        return False

def update_registry_floor_info(floor_description):
    try:
        with open(REGISTRY_JSON_PATH, "r") as f:
            registry_data = json.load(f)
        
        if "regions" in registry_data and "azansaleh_1" in registry_data["regions"]:
            registry_data["regions"]["azansaleh_1"]["floor_markings"] = floor_description
            registry_data["regions"]["azansaleh_1"]["floor_y_level"] = FLOOR_Y
            
            with open(REGISTRY_JSON_PATH, "w") as f:
                json.dump(registry_data, f, indent=4)
            print("Successfully updated floor markings in player_regions_registry.json.")
    except Exception as e:
        print(f"Warning: Could not update registry: {e}")

def fill_floor(dry_run=False, undo=False):
    if undo:
        cmd = f"fill {MIN_X} {FLOOR_Y} {MIN_Z} {MAX_X} {FLOOR_Y} {MAX_Z} minecraft:air"
        print(f"Reverting floor level Y={FLOOR_Y} of `azansaleh_1` to air...")
    else:
        cmd = f"fill {MIN_X} {FLOOR_Y} {MIN_Z} {MAX_X} {FLOOR_Y} {MAX_Z} minecraft:dirt"
        print(f"Filling floor level Y={FLOOR_Y} of `azansaleh_1` with Dirt...")

    success = send_exaroton_command(cmd, dry_run=dry_run)
    if success:
        if undo:
            clear_loot_cmd = f"kill @e[type=item,x=1062,y={FLOOR_Y},z=-152,distance=..35]"
            send_exaroton_command(clear_loot_cmd, dry_run=dry_run)
            update_registry_floor_info("None")
            print(f"Successfully reverted floor to air and cleared dropped item loot.")
        else:
            update_registry_floor_info("Dirt base floor")
            print(f"Successfully filled floor with Dirt.")
    return success

def main():
    parser = argparse.ArgumentParser(description="Fill base floor of azansaleh_1 with Dirt at Y=63.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying world")
    parser.add_argument("--undo", action="store_true", help="Undo floor filling by setting back to air and clearing items")
    args = parser.parse_args()

    fill_floor(dry_run=args.dry_run, undo=args.undo)

if __name__ == "__main__":
    main()
