#!/usr/bin/env python3
"""
Fill Old Floor of azansaleh_1 with Dirt Script
- Fills the old base floor level of 'azansaleh_1' (Y=62) with Dirt.
- Bounds: X: 1040..1084, Z: -174..-130, Y: 62.
- Supports dry-run and undo (--undo reverts Y=62 back to grass_block and clears dropped items).
"""

import os
import sys
import json
import subprocess
import argparse

PLUGINS_DIR = "/Users/hanansaleh/Downloads/plugins"

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
OLD_FLOOR_Y = 62

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

def fill_old_floor(dry_run=False, undo=False):
    if undo:
        # Revert floor to grass_block
        cmd = f"fill {MIN_X} {OLD_FLOOR_Y} {MIN_Z} {MAX_X} {OLD_FLOOR_Y} {MAX_Z} minecraft:grass_block"
        print(f"Reverting old floor level Y={OLD_FLOOR_Y} of `azansaleh_1` to grass_block...")
    else:
        # Fill floor with dirt
        cmd = f"fill {MIN_X} {OLD_FLOOR_Y} {MIN_Z} {MAX_X} {OLD_FLOOR_Y} {MAX_Z} minecraft:dirt"
        print(f"Filling old floor level Y={OLD_FLOOR_Y} of `azansaleh_1` with dirt...")

    success = send_exaroton_command(cmd, dry_run=dry_run)
    if success:
        if undo:
            # Clear dropped item loot in the affected area
            clear_loot_cmd = f"kill @e[type=item,x=1062,y={OLD_FLOOR_Y},z=-152,distance=..35]"
            send_exaroton_command(clear_loot_cmd, dry_run=dry_run)
            print(f"Successfully reverted old floor to grass_block and cleared dropped item loot.")
        else:
            print(f"Successfully filled old floor Y={OLD_FLOOR_Y} with dirt.")
    return success

def main():
    parser = argparse.ArgumentParser(description="Fill old base floor of azansaleh_1 (Y=62) with dirt.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying world")
    parser.add_argument("--undo", action="store_true", help="Undo dirt filling by setting back to grass_block and clearing items")
    args = parser.parse_args()

    fill_old_floor(dry_run=args.dry_run, undo=args.undo)

if __name__ == "__main__":
    main()
