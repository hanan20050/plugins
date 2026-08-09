#!/usr/bin/env python3
"""
Set Azan Saleh's entire region base floor (Y=62) to a uniform concrete color (minecraft:white_concrete).

Region bounds:
X: 1241 to 1255
Z: -219 to -191
Y: 62

Supports --color, --dry-run, and --undo options.
"""

import os
import sys
import json
import subprocess
import argparse

BACKUP_FILE = "azansaleh_uniform_floor_history.json"

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

def apply_uniform_floor(color="minecraft:white_concrete", dry_run=False):
    if not color.startswith("minecraft:"):
        color = f"minecraft:{color}"

    cmd = f"fill {MIN_X} {Y} {MIN_Z} {MAX_X} {Y} {MAX_Z} {color}"
    print(f"Setting Azan Saleh's entire region floor at Y={Y} to {color}...")
    print(f"Executing: {cmd}")
    
    success = send_exaroton_command(cmd, dry_run=dry_run)
    if success and not dry_run:
        with open(BACKUP_FILE, "w") as f:
            json.dump({"cmd": cmd, "color": color}, f, indent=2)
        print(f"Floor updated successfully! History saved to {BACKUP_FILE}")

def undo(dry_run=False):
    print("Undoing uniform floor update (restoring floor to dirt)...")
    cmd = f"fill {MIN_X} {Y} {MIN_Z} {MAX_X} {Y} {MAX_Z} minecraft:dirt"
    send_exaroton_command(cmd, dry_run=dry_run)
    print("Floor restored to minecraft:dirt.")

def main():
    parser = argparse.ArgumentParser(description="Set Azan Saleh's entire floor to uniform concrete")
    parser.add_argument("--color", default="minecraft:white_concrete", help="Concrete color to use")
    parser.add_argument("--dry-run", action="store_true", help="Print command without executing")
    parser.add_argument("--undo", action="store_true", help="Undo floor update")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        apply_uniform_floor(color=args.color, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
