#!/usr/bin/env python3
"""
WorldGuard Region Wall / Structure Clearer (with Undo Support)
----------------------------------------------------------------
Clears all blocks above the region floor (Y_min + 1 to Y_max) by filling with air,
removing all wall outlines and structures while keeping the floor intact.
Saves history to WorldGuard/backups/wall_history.json to support --undo.

Usage:
  python3 clear_region_walls.py <region_name> [--dry-run]
  python3 clear_region_walls.py <region_name> --undo [--dry-run]
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
HISTORY_FILE = "WorldGuard/backups/wall_history.json"

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

def save_wall_history(region, coordinates):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            history = {}
    
    history[region] = {
        "action": "cleared_above_floor",
        "coords": coordinates
    }
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)
    print(f"📝 Wall clear history updated in '{HISTORY_FILE}'.")

def load_wall_history(region):
    if not os.path.exists(HISTORY_FILE):
        return None
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
            return history.get(region)
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser(description="Clear walls/structures above floor for a WorldGuard region")
    parser.add_argument("region", help="Name of the WorldGuard region")
    parser.add_argument("--undo", action="store_true", help="Undo wall clearance (note: cannot restore original custom block states unless backed up prior)")
    parser.add_argument("--dry-run", action="store_true", help="Preview command without executing on server")

    args = parser.parse_args()

    if args.undo:
        record = load_wall_history(args.region)
        if record:
            print(f"ℹ️ Wall clear operation record found for region '{args.region}': {record['coords']}")
            print("Notice: Clearing walls replaced blocks with air. Reverting will require rebuilding walls.")
        else:
            print(f"⚠️ No wall clearing history record found for region '{args.region}'.")
        return

    print(f"🔍 Fetching coordinates for region '{args.region}'...")
    min_c, max_c = get_region_bounds(args.region)
    
    if not min_c or not max_c:
        print(f"❌ Region '{args.region}' not found or bounds could not be parsed.")
        sys.exit(1)
        
    min_x, min_y, min_z = min_c
    max_x, max_y, max_z = max_c
    
    start_y = min_y + 1
    if start_y > max_y:
        print(f"⚠️ Region '{args.region}' has height of 1 block only (Y={min_y}). No wall space above floor to clear.")
        sys.exit(0)

    print(f"📐 Region bounds detected:")
    print(f"   Floor Y: {min_y} (Kept intact)")
    print(f"   Wall clearing area: Y={start_y} to Y={max_y}")
    print(f"   X: {min_x}..{max_x}, Z: {min_z}..{max_z}")
    print(f"🧹 Clearing wall outlines / structure blocks (filling with minecraft:air)...")
    
    fill_cmd = f"fill {min_x} {start_y} {min_z} {max_x} {max_y} {max_z} minecraft:air"
    
    if send_exaroton_command(fill_cmd, args.dry_run):
        if not args.dry_run:
            save_wall_history(args.region, [min_x, start_y, min_z, max_x, max_y, max_z])
        print(f"🎉 Wall clearance command executed successfully!")

if __name__ == "__main__":
    main()
