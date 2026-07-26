#!/usr/bin/env python3
"""
Draw Yellow Concrete 'A' Script
- Draws a large capital letter 'A' with Yellow Concrete at the center of the 'azansaleh_1' region base floor (Y=63).
- Coordinates: Center (1062, -152), Width: 9 blocks (1058..1066), Height: 11 blocks (-157..-147).
- Supports --undo to restore the affected floor blocks back to Red Concrete.
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

def draw_a(dry_run=False, undo=False):
    material = "minecraft:dirt" if undo else "minecraft:yellow_concrete"
    
    commands = [
        # Left Leg
        f"fill 1058 {FLOOR_Y} -157 1058 {FLOOR_Y} -147 {material}",
        # Right Leg
        f"fill 1066 {FLOOR_Y} -157 1066 {FLOOR_Y} -147 {material}",
        # Top Bar
        f"fill 1058 {FLOOR_Y} -157 1066 {FLOOR_Y} -157 {material}",
        # Crossbar
        f"fill 1058 {FLOOR_Y} -152 1066 {FLOOR_Y} -152 {material}"
    ]
    
    action_str = "Undoing Yellow 'A' (restoring Red Concrete)..." if undo else "Drawing Yellow Concrete 'A'..."
    print(action_str)
    
    success = True
    for cmd in commands:
        if not send_exaroton_command(cmd, dry_run=dry_run):
            success = False

    if success:
        if undo:
            # Clear dropped item loot to prevent clutter
            clear_loot_cmd = f"kill @e[type=item,x=1062,y={FLOOR_Y},z=-152,distance=..20]"
            send_exaroton_command(clear_loot_cmd, dry_run=dry_run)
            print("Successfully restored floor to Red Concrete and cleared dropped items.")
        else:
            print("Successfully drew Yellow Concrete 'A'!")
    return success

def main():
    parser = argparse.ArgumentParser(description="Draw Yellow Concrete 'A' in the center of azansaleh_1.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying world")
    parser.add_argument("--undo", action="store_true", help="Undo drawing by restoring the base Red Concrete floor")
    args = parser.parse_args()

    draw_a(dry_run=args.dry_run, undo=args.undo)

if __name__ == "__main__":
    main()
