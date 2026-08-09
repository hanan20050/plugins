#!/usr/bin/env python3
"""
Fill floor level (Y=78) of moved `combined_region` with dirt.
Bounds: X: 1293..1300, Z: -230..-222, Y: 78.

Supports --undo and --dry-run for strict rollback compliance.
"""

import os
import sys
import json
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

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or "cEuS61sZvNEFS3aB"

MIN_X, MAX_X = 1293, 1300
MIN_Z, MAX_Z = -230, -222
FLOOR_Y = 78

HISTORY_FILE = "WorldGuard/backups/moved_region_dirt_floor_history.json"

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

def record_history(command, action):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                history = json.load(f)
            except Exception:
                history = []
    history.append({"action": action, "command": command})
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def fill_floor_dirt(dry_run=False, undo=False):
    if undo:
        cmd = f"fill {MIN_X} {FLOOR_Y} {MIN_Z} {MAX_X} {FLOOR_Y} {MAX_Z} minecraft:white_concrete"
        print(f"Reverting floor level Y={FLOOR_Y} of moved `combined_region` to white concrete...")
        success = send_exaroton_command(cmd, dry_run=dry_run)
        if success and not dry_run:
            record_history(cmd, "undo")
            print(f"Successfully reverted Y={FLOOR_Y} floor to white concrete.")
    else:
        cmd = f"fill {MIN_X} {FLOOR_Y} {MIN_Z} {MAX_X} {FLOOR_Y} {MAX_Z} minecraft:dirt"
        print(f"Filling floor level Y={FLOOR_Y} of moved `combined_region` (X: {MIN_X}..{MAX_X}, Z: {MIN_Z}..{MAX_Z}) with dirt...")
        success = send_exaroton_command(cmd, dry_run=dry_run)
        if success and not dry_run:
            record_history(cmd, "fill_dirt")
            print(f"Successfully filled Y={FLOOR_Y} floor layer with dirt.")

def main():
    parser = argparse.ArgumentParser(description="Fill floor of moved combined_region with dirt.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying world")
    parser.add_argument("--undo", action="store_true", help="Undo dirt filling by resetting Y=78 floor back to white concrete")
    args = parser.parse_args()

    fill_floor_dirt(dry_run=args.dry_run, undo=args.undo)

if __name__ == "__main__":
    main()
