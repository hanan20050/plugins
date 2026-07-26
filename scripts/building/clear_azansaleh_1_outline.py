#!/usr/bin/env python3
"""
Clear Outline for azansaleh_1 Script
- Fills the perimeter borders (walls) of the region 'azansaleh_1' with air from the base floor (Y=63) up to Y=256.
- Bounds: X: 1040..1084, Z: -174..-130, Y: 63..256.
- Clears dropped items in the region area afterward to prevent lag/clutter.
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
MIN_Y, MAX_Y = 64, 256

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

def clear_outline(dry_run=False):
    # To avoid block fill limit (32768 blocks), we split the fill command per wall.
    # Each wall is 45 length * 1 width * 194 height = 8730 blocks, which is safely below 32768.
    commands = [
        # North Wall
        f"fill {MIN_X} {MIN_Y} {MIN_Z} {MAX_X} {MAX_Y} {MIN_Z} minecraft:air",
        # South Wall
        f"fill {MIN_X} {MIN_Y} {MAX_Z} {MAX_X} {MAX_Y} {MAX_Z} minecraft:air",
        # West Wall
        f"fill {MIN_X} {MIN_Y} {MIN_Z} {MIN_X} {MAX_Y} {MAX_Z} minecraft:air",
        # East Wall
        f"fill {MAX_X} {MIN_Y} {MIN_Z} {MAX_X} {MAX_Y} {MAX_Z} minecraft:air"
    ]
    
    print("Clearing region outline (perimeter walls) with air...")
    success = True
    for cmd in commands:
        if not send_exaroton_command(cmd, dry_run=dry_run):
            success = False

    if success:
        # ALWAYS immediately clear dropped item loot in the affected area to prevent clutter
        clear_loot_cmd = f"kill @e[type=item,x=1062,y=100,z=-152,distance=..35]"
        send_exaroton_command(clear_loot_cmd, dry_run=dry_run)
        print("Successfully cleared outline with air and cleared dropped items.")
    return success

def main():
    parser = argparse.ArgumentParser(description="Clear outline walls of azansaleh_1 with air.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying world")
    args = parser.parse_args()

    clear_outline(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
