#!/usr/bin/env python3
"""
Divide Azan Saleh's region (`azansalehhh`) base floor (Y=62) into 4 quadrant concrete colors:
- NW Quadrant: Red Concrete
- NE Quadrant: Blue Concrete
- SW Quadrant: Yellow Concrete
- SE Quadrant: Lime Concrete

Region bounds:
X: 1241..1255
Y: 62
Z: -219..-191

Supports --dry-run and --undo options.
"""

import os
import sys
import json
import subprocess
import argparse

BACKUP_FILE = "azansaleh_floor_division_history.json"

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or "cEuS61sZvNEFS3aB"

# Quadrant boundaries at Y=62
Y = 62

QUADRANTS = [
    {
        "name": "North-West (NW)",
        "color": "minecraft:red_concrete",
        "min_x": 1241, "max_x": 1247,
        "min_z": -219, "max_z": -205
    },
    {
        "name": "North-East (NE)",
        "color": "minecraft:blue_concrete",
        "min_x": 1248, "max_x": 1255,
        "min_z": -219, "max_z": -205
    },
    {
        "name": "South-West (SW)",
        "color": "minecraft:yellow_concrete",
        "min_x": 1241, "max_x": 1247,
        "min_z": -204, "max_z": -191
    },
    {
        "name": "South-East (SE)",
        "color": "minecraft:lime_concrete",
        "min_x": 1248, "max_x": 1255,
        "min_z": -204, "max_z": -191
    }
]

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

def apply_quadrants(dry_run=False):
    history = []
    print(f"Dividing Azan Saleh's base floor (Y={Y}) into 4 concrete quadrants...")
    for q in QUADRANTS:
        cmd = f"fill {q['min_x']} {Y} {q['min_z']} {q['max_x']} {Y} {q['max_z']} {q['color']}"
        print(f"Applying {q['name']}: {cmd}")
        success = send_exaroton_command(cmd, dry_run=dry_run)
        if success:
            history.append(cmd)
        else:
            print(f"[WARNING] Command failed for {q['name']}")
    
    if not dry_run:
        with open(BACKUP_FILE, "w") as f:
            json.dump({"applied_commands": history}, f, indent=2)
        print(f"Saved floor command history to {BACKUP_FILE}")

def undo(dry_run=False):
    print(f"Undoing Azan Saleh's 4-color floor division (restoring to white_concrete)...")
    cmd = f"fill 1241 {Y} -219 1255 {Y} -191 minecraft:white_concrete"
    send_exaroton_command(cmd, dry_run=dry_run)
    print("Floor restored to minecraft:white_concrete.")

def main():
    parser = argparse.ArgumentParser(description="Divide Azan Saleh's floor into 4 concrete colors")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--undo", action="store_true", help="Undo floor changes")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        apply_quadrants(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
