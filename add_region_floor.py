#!/usr/bin/env python3
"""
WorldGuard Region Floor Generator (with Undo Support)
------------------------------------------------------
Finds the bottom-most layer (floor) of a WorldGuard region and executes
a Minecraft `/fill` command via Exaroton console to instantly create a floor.
Maintains a local history database in `WorldGuard/backups/floor_history.json`
to support a strict `--undo` operation.

Usage:
  python3 add_region_floor.py <region_name> <material> [--dry-run]
  python3 add_region_floor.py <region_name> --undo [--dry-run]

Examples:
  # Create oak planks floor:
  python3 add_region_floor.py mustafahacker67 oak_planks

  # Undo the oak planks floor:
  python3 add_region_floor.py mustafahacker67 --undo
"""

import os
import sys
import json
import re
import subprocess
import argparse

# Load Environment Configuration (.env)
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID")

REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"
HISTORY_FILE = "WorldGuard/backups/floor_history.json"

def send_exaroton_command(cmd, dry_run=False):
    if dry_run:
        print(f"[DRY-RUN] Console command: {cmd}")
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
        if data.get("success"):
            print(f"✅ Executed console command: {cmd}")
            return True
        else:
            print(f"❌ Exaroton Command Error: {data.get('error')}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def pull_region_file():
    pull_cmd = [sys.executable, "sync.py", "pull", REGIONS_FILE]
    subprocess.run(pull_cmd, capture_output=True)

def get_region_bounds(region_name):
    pull_region_file()
    if not os.path.exists(REGIONS_FILE):
        print("❌ Could not locate regions.yml.")
        sys.exit(1)

    min_coords = None
    max_coords = None
    current_region = None

    with open(REGIONS_FILE, "r") as f:
        for line in f:
            reg_match = re.match(r"^ {4}([a-zA-Z0-9_\-]+):", line)
            if reg_match:
                current_region = reg_match.group(1)
                continue

            if current_region == region_name:
                if "min:" in line:
                    m = re.search(r"x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)", line)
                    if m:
                        min_coords = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
                elif "max:" in line:
                    m = re.search(r"x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)", line)
                    if m:
                        max_coords = (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    return min_coords, max_coords

def save_floor_history(region, material, coordinates):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            history = {}
    
    # Save the floor change
    history[region] = {
        "material": material,
        "coords": coordinates
    }
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)
    print(f"📝 Floor history updated in '{HISTORY_FILE}'.")

def load_floor_history(region):
    if not os.path.exists(HISTORY_FILE):
        return None
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
            return history.get(region)
    except Exception:
        return None

def remove_floor_history(region):
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
            if region in history:
                del history[region]
            with open(HISTORY_FILE, "w") as f:
                json.dump(history, f, indent=4)
        except Exception:
            pass

def main():
    parser = argparse.ArgumentParser(description="Generate/Undo floor for a WorldGuard region using console commands")
    parser.add_argument("region", help="Name of the WorldGuard region")
    parser.add_argument("material", nargs="?", help="Minecraft block type (e.g. grass_block, oak_planks). Optional if running --undo")
    parser.add_argument("--undo", action="store_true", help="Undo the last floor generation for this region (replaces it with grass_block or air)")
    parser.add_argument("--dry-run", action="store_true", help="Preview command without executing on the server")

    args = parser.parse_args()

    if args.undo:
        # Perform Undo operation
        record = load_floor_history(args.region)
        if record:
            min_x, floor_y, min_z, max_x, max_z = record["coords"]
            # To undo, we usually replace the floor with grass_block or air (since it was likely grass/air before)
            # We default to grass_block as it is a safe base, or air if requested. Let's use grass_block
            undo_material = "grass_block"
            print(f"🔄 Reverting floor generation for region '{args.region}' at Y={floor_y} to '{undo_material}'...")
            undo_cmd = f"fill {min_x} {floor_y} {min_z} {max_x} {floor_y} {max_z} minecraft:{undo_material}"
            if send_exaroton_command(undo_cmd, args.dry_run):
                if not args.dry_run:
                    remove_floor_history(args.region)
                    print(f"🎉 Floor undone successfully!")
        else:
            # Revert fallback without history
            print(f"⚠️ No floor generation history found for region '{args.region}'.")
            print("🔍 Fetching bounds to attempt fallback undo (filling bottom layer with air)...")
            min_c, max_c = get_region_bounds(args.region)
            if min_c and max_c:
                min_x, min_y, min_z = min_c
                max_x, max_y, max_z = max_c
                undo_cmd = f"fill {min_x} {min_y} {min_z} {max_x} {min_y} {max_z} minecraft:air"
                if send_exaroton_command(undo_cmd, args.dry_run):
                    print(f"🎉 Fallback floor undo completed (filled bottom layer with air).")
            else:
                print("❌ Region bounds not found. Cannot perform fallback undo.")
                sys.exit(1)
        return

    # Check that material is provided when not undoing
    if not args.material:
        print("❌ Error: material argument is required unless running with --undo")
        sys.exit(1)

    print(f"🔍 Fetching coordinates for region '{args.region}'...")
    min_c, max_c = get_region_bounds(args.region)
    
    if not min_c or not max_c:
        print(f"❌ Region '{args.region}' not found or bounds could not be parsed.")
        sys.exit(1)
        
    min_x, min_y, min_z = min_c
    max_x, max_y, max_z = max_c
    floor_y = min_y
    
    print(f"📐 Region bounds detected:")
    print(f"   Min: X={min_x}, Y={min_y}, Z={min_z}")
    print(f"   Max: X={max_x}, Y={max_y}, Z={max_z}")
    print(f"🧱 Placing '{args.material}' floor at Y={floor_y}...")
    
    fill_cmd = f"fill {min_x} {floor_y} {min_z} {max_x} {floor_y} {max_z} minecraft:{args.material.replace('minecraft:', '')}"
    
    if send_exaroton_command(fill_cmd, args.dry_run):
        if not args.dry_run:
            save_floor_history(args.region, args.material, [min_x, floor_y, min_z, max_x, max_z])
        print(f"🎉 Floor generation command sent successfully!")

if __name__ == "__main__":
    main()
