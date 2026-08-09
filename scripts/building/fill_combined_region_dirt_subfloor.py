#!/usr/bin/env python3
"""
Fill dirt floor 2 blocks below the floor level (Y=76) for `combined_region`.
Region bounds: X: 1292..1299, Z: -230..-222, Y: 76.

Supports --undo and --dry-run options for strict rollback compliance.
"""

import os
import sys
import json
import subprocess
import argparse

# Credentials and constants
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

MIN_X, MAX_X = 1292, 1299
MIN_Z, MAX_Z = -230, -222
TARGET_Y = 76  # 2 blocks below floor Y=78

HISTORY_FILE = "WorldGuard/backups/dirt_subfloor_y76_history.json"

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

def fill_subfloor_dirt(dry_run=False, undo=False):
    if undo:
        cmd = f"fill {MIN_X} {TARGET_Y} {MIN_Z} {MAX_X} {TARGET_Y} {MAX_Z} minecraft:air"
        print(f"Reverting 2-block subfloor level Y={TARGET_Y} of `combined_region` to air...")
        success = send_exaroton_command(cmd, dry_run=dry_run)
        if success and not dry_run:
            record_history(cmd, "undo")
            print(f"Successfully reverted Y={TARGET_Y} subfloor to air.")
    else:
        cmd = f"fill {MIN_X} {TARGET_Y} {MIN_Z} {MAX_X} {TARGET_Y} {MAX_Z} minecraft:dirt"
        print(f"Filling 2-block subfloor level Y={TARGET_Y} of `combined_region` (X: {MIN_X}..{MAX_X}, Z: {MIN_Z}..{MAX_Z}) with dirt...")
        success = send_exaroton_command(cmd, dry_run=dry_run)
        if success and not dry_run:
            record_history(cmd, "fill_dirt")
            print(f"Successfully filled Y={TARGET_Y} subfloor layer with dirt.")

def main():
    parser = argparse.ArgumentParser(description="Fill dirt floor 2 blocks below main floor for combined_region.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying world")
    parser.add_argument("--undo", action="store_true", help="Undo dirt filling by resetting Y=76 subfloor back to air")
    args = parser.parse_args()

    fill_subfloor_dirt(dry_run=args.dry_run, undo=args.undo)

if __name__ == "__main__":
    main()
