#!/usr/bin/env python3
"""
WorldGuard Region Floor Generator
---------------------------------
Finds the bottom-most layer (floor) of a WorldGuard region and executes
a Minecraft `/fill` command via Exaroton console to instantly create a floor.

Usage:
  python3 add_region_floor.py <region_name> <material> [--dry-run]

Example:
  python3 add_region_floor.py mustafahacker67 oak_planks
  python3 add_region_floor.py hanansaleh smooth_stone
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

def main():
    parser = argparse.ArgumentParser(description="Generate floor for a WorldGuard region using console commands")
    parser.add_argument("region", help="Name of the WorldGuard region")
    parser.add_argument("material", help="Minecraft block type (e.g. grass_block, oak_planks, smooth_stone)")
    parser.add_argument("--dry-run", action="store_true", help="Preview the /fill command without executing on the server")

    args = parser.parse_args()
    
    print(f"🔍 Fetching coordinates for region '{args.region}'...")
    min_c, max_c = get_region_bounds(args.region)
    
    if not min_c or not max_c:
        print(f"❌ Region '{args.region}' not found or bounds could not be parsed.")
        sys.exit(1)
        
    min_x, min_y, min_z = min_c
    max_x, max_y, max_z = max_c
    
    # Bottom layer Y-level is min_y
    floor_y = min_y
    
    print(f"📐 Region bounds detected:")
    print(f"   Min: X={min_x}, Y={min_y}, Z={min_z}")
    print(f"   Max: X={max_x}, Y={max_y}, Z={max_z}")
    print(f"🧱 Placing '{args.material}' floor at Y={floor_y}...")
    
    # Minecraft fill command syntax: /fill <x1> <y1> <z1> <x2> <y2> <z2> <block>
    fill_cmd = f"fill {min_x} {floor_y} {min_z} {max_x} {floor_y} {max_z} minecraft:{args.material.replace('minecraft:', '')}"
    
    if send_exaroton_command(fill_cmd, args.dry_run):
        print(f"🎉 Floor generation command sent successfully!")

if __name__ == "__main__":
    main()
