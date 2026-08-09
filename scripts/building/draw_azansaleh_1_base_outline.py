#!/usr/bin/env python3
"""
Draw Base Outline for azansaleh_1 Script
- Fills the perimeter outline frame of the region 'azansaleh_1' on the base floor level (Y=63) with Red Concrete.
- Bounds: X: 1040..1084, Z: -174..-130, Y: 63.
- Supports dry-run and undo (--undo reverts Y=63 border back to dirt and clears dropped items).
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

def draw_outline(dry_run=False, undo=False):
    material = "minecraft:dirt" if undo else "minecraft:red_concrete"
    
    commands = [
        # North Edge
        f"fill {MIN_X} {FLOOR_Y} {MIN_Z} {MAX_X} {FLOOR_Y} {MIN_Z} {material}",
        # South Edge
        f"fill {MIN_X} {FLOOR_Y} {MAX_Z} {MAX_X} {FLOOR_Y} {MAX_Z} {material}",
        # West Edge
        f"fill {MIN_X} {FLOOR_Y} {MIN_Z} {MIN_X} {FLOOR_Y} {MAX_Z} {material}",
        # East Edge
        f"fill {MAX_X} {FLOOR_Y} {MIN_Z} {MAX_X} {FLOOR_Y} {MAX_Z} {material}"
    ]
    
    action_str = "Undoing Red Concrete outline (restoring Dirt)..." if undo else "Drawing Red Concrete base outline..."
    print(action_str)
    
    success = True
    for cmd in commands:
        if not send_exaroton_command(cmd, dry_run=dry_run):
            success = False

    if success:
        # Clear dropped items in the area
        clear_loot_cmd = f"kill @e[type=item,x=1062,y={FLOOR_Y},z=-152,distance=..35]"
        send_exaroton_command(clear_loot_cmd, dry_run=dry_run)
        if undo:
            print("Successfully restored outline to Dirt and cleared dropped items.")
        else:
            print("Successfully drew Red Concrete base outline!")
    return success

def main():
    parser = argparse.ArgumentParser(description="Draw Red Concrete base outline for azansaleh_1.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying world")
    parser.add_argument("--undo", action="store_true", help="Undo outline by setting it back to dirt")
    args = parser.parse_args()

    draw_outline(dry_run=args.dry_run, undo=args.undo)

if __name__ == "__main__":
    main()
