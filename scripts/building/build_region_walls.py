#!/usr/bin/env python3
"""
WorldGuard Region Wall Generator (with Undo Support)
-----------------------------------------------------
Builds perimeter walls for a WorldGuard region from Y_min + 1 up to Y_min + height (default 3 blocks).
Maintains history in WorldGuard/backups/wall_build_history.json to support --undo.

Usage:
  python3 build_region_walls.py <region_name> <material> [--height 3] [--dry-run]
  python3 build_region_walls.py <region_name> --undo [--dry-run]
"""

import os
import sys
import json
import re
import subprocess
import argparse

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
HISTORY_FILE = "WorldGuard/backups/wall_build_history.json"

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

def save_build_history(region, material, height, coordinates):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            history = {}
    
    history[region] = {
        "material": material,
        "height": height,
        "coords": coordinates
    }
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)
    print(f"📝 Wall build history saved in '{HISTORY_FILE}'.")

def load_build_history(region):
    if not os.path.exists(HISTORY_FILE):
        return None
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
            return history.get(region)
    except Exception:
        return None

def remove_build_history(region):
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
    parser = argparse.ArgumentParser(description="Build 3-block high perimeter walls for a WorldGuard region")
    parser.add_argument("region", help="Name of the WorldGuard region")
    parser.add_argument("material", nargs="?", help="Minecraft block type (e.g. white_concrete, smooth_quartz)")
    parser.add_argument("--height", type=int, default=3, help="Height of the wall in blocks (default: 3)")
    parser.add_argument("--undo", action="store_true", help="Undo perimeter wall construction (fills walls with air)")
    parser.add_argument("--dry-run", action="store_true", help="Preview commands without executing on server")

    args = parser.parse_args()

    min_c, max_c = get_region_bounds(args.region)
    if not min_c or not max_c:
        print(f"❌ Region '{args.region}' not found.")
        sys.exit(1)

    min_x, min_y, min_z = min_c
    max_x, max_y, max_z = max_c

    start_y = min_y + 1
    end_y = start_y + args.height - 1

    if args.undo:
        print(f"🔄 Undoing perimeter walls for region '{args.region}' (clearing Y={start_y} to Y={end_y} perimeter)...")
        cmds = [
            f"fill {min_x} {start_y} {min_z} {max_x} {end_y} {min_z} minecraft:air", # North
            f"fill {min_x} {start_y} {max_z} {max_x} {end_y} {max_z} minecraft:air", # South
            f"fill {min_x} {start_y} {min_z} {min_x} {end_y} {max_z} minecraft:air", # West
            f"fill {max_x} {start_y} {min_z} {max_x} {end_y} {max_z} minecraft:air"  # East
        ]
        success = True
        for cmd in cmds:
            if not send_exaroton_command(cmd, args.dry_run):
                success = False
        if success and not args.dry_run:
            remove_build_history(args.region)
            print(f"🎉 Wall undo completed!")
        return

    if not args.material:
        print("❌ Material is required unless using --undo.")
        sys.exit(1)

    mat = f"minecraft:{args.material.replace('minecraft:', '')}"
    print(f"📐 Building {args.height}-block high perimeter walls of '{mat}' for region '{args.region}'...")
    print(f"   Floor Y: {min_y}")
    print(f"   Wall Y Range: {start_y} to {end_y}")
    print(f"   Perimeter: X={min_x}..{max_x}, Z={min_z}..{max_z}")

    wall_cmds = [
        f"fill {min_x} {start_y} {min_z} {max_x} {end_y} {min_z} {mat}", # North
        f"fill {min_x} {start_y} {max_z} {max_x} {end_y} {max_z} {mat}", # South
        f"fill {min_x} {start_y} {min_z} {min_x} {end_y} {max_z} {mat}", # West
        f"fill {max_x} {start_y} {min_z} {max_x} {end_y} {max_z} {mat}"  # East
    ]

    success = True
    for cmd in wall_cmds:
        if not send_exaroton_command(cmd, args.dry_run):
            success = False

    if success:
        if not args.dry_run:
            save_build_history(args.region, args.material, args.height, [min_x, start_y, end_y, min_z, max_z])
        print(f"🎉 Perimeter walls built successfully!")

if __name__ == "__main__":
    main()
