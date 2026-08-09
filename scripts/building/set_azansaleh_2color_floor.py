#!/usr/bin/env python3
"""
Divide Azan Saleh's region floor (Y=62) into 2 equal color sections (2-color concrete):
- Section 1 (North Half, Z: -219 to -205): White Concrete
- Section 2 (South Half, Z: -204 to -191): Cyan Concrete

Region Bounds:
X: 1241 to 1255 (15 blocks wide)
Z: -219 to -191 (29 blocks long)
Y: 62

Supports --color1, --color2, --dry-run, and --undo options.
"""

import os
import sys
import json
import subprocess
import argparse

BACKUP_FILE = "azansaleh_2color_floor_history.json"

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

MIN_X, MAX_X = 1241, 1255
MIN_Z, MAX_Z = -219, -191
Y = 62

# Midpoint split along Z-axis
NORTH_MIN_Z, NORTH_MAX_Z = -219, -205
SOUTH_MIN_Z, SOUTH_MAX_Z = -204, -191

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

def apply_2color_floor(color1="minecraft:white_concrete", color2="minecraft:cyan_concrete", dry_run=False):
    if not color1.startswith("minecraft:"):
        color1 = f"minecraft:{color1}"
    if not color2.startswith("minecraft:"):
        color2 = f"minecraft:{color2}"

    print(f"Dividing Azan Saleh's floor (Y={Y}) into 2 concrete colors ({color1} & {color2})...")
    
    cmd1 = f"fill {MIN_X} {Y} {NORTH_MIN_Z} {MAX_X} {Y} {NORTH_MAX_Z} {color1}"
    cmd2 = f"fill {MIN_X} {Y} {SOUTH_MIN_Z} {MAX_X} {Y} {SOUTH_MAX_Z} {color2}"
    
    cmds = [cmd1, cmd2]
    history = []
    
    for cmd in cmds:
        print(f"Executing: {cmd}")
        success = send_exaroton_command(cmd, dry_run=dry_run)
        if success:
            history.append(cmd)

    if not dry_run:
        with open(BACKUP_FILE, "w") as f:
            json.dump({"applied_commands": history, "color1": color1, "color2": color2}, f, indent=2)
        print(f"Floor updated successfully! History saved to {BACKUP_FILE}")

def undo(dry_run=False):
    print("Undoing 2-color floor update (restoring floor to uniform white_concrete)...")
    cmd = f"fill {MIN_X} {Y} {MIN_Z} {MAX_X} {Y} {MAX_Z} minecraft:white_concrete"
    send_exaroton_command(cmd, dry_run=dry_run)
    print("Floor restored to minecraft:white_concrete.")

def main():
    parser = argparse.ArgumentParser(description="Divide Azan Saleh's floor into 2 concrete colors")
    parser.add_argument("--color1", default="minecraft:white_concrete", help="First concrete color (North half)")
    parser.add_argument("--color2", default="minecraft:cyan_concrete", help="Second concrete color (South half)")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--undo", action="store_true", help="Undo floor update")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        apply_2color_floor(color1=args.color1, color2=args.color2, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
