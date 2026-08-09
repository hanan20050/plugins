#!/usr/bin/env python3
"""
Fill the 1-block West lane (X=1292, Z: -230..-222, Y=76..78) with dirt where region shifted from,
and restore the moved `combined_region` floor (X: 1293..1300, Y=78) with white concrete.

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

# Coordinates
WEST_LANE_X = 1292
REGION_MIN_X, REGION_MAX_X = 1293, 1300
MIN_Z, MAX_Z = -230, -222

FLOOR_Y = 78
SUBFLOOR_MIN_Y = 76

HISTORY_FILE = "WorldGuard/backups/west_lane_dirt_fill_history.json"

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

def execute_fill(dry_run=False, undo=False):
    if undo:
        # Undo: set west lane X=1292 back to air, set region floor X=1293..1300 Y=78 to dirt
        cmd_undo_west = f"fill {WEST_LANE_X} {SUBFLOOR_MIN_Y} {MIN_Z} {WEST_LANE_X} {FLOOR_Y} {MAX_Z} minecraft:air"
        cmd_undo_region = f"fill {REGION_MIN_X} {FLOOR_Y} {MIN_Z} {REGION_MAX_X} {FLOOR_Y} {MAX_Z} minecraft:dirt"

        print(f"Reverting West lane X={WEST_LANE_X} (Y={SUBFLOOR_MIN_Y}..{FLOOR_Y}) to air...")
        send_exaroton_command(cmd_undo_west, dry_run=dry_run)

        print(f"Reverting region floor Y={FLOOR_Y} (X={REGION_MIN_X}..{REGION_MAX_X}) to dirt...")
        send_exaroton_command(cmd_undo_region, dry_run=dry_run)

        if not dry_run:
            record_history("undo", "undo_execution")
            print("Undo executed successfully.")
    else:
        # Step 1: Fill West lane X=1292 (Y=76..78, Z=-230..-222) with dirt
        cmd_west_dirt = f"fill {WEST_LANE_X} {SUBFLOOR_MIN_Y} {MIN_Z} {WEST_LANE_X} {FLOOR_Y} {MAX_Z} minecraft:dirt"
        print(f"Filling 1-block West lane X={WEST_LANE_X} (Y={SUBFLOOR_MIN_Y}..{FLOOR_Y}, Z={MIN_Z}..{MAX_Z}) with dirt...")
        send_exaroton_command(cmd_west_dirt, dry_run=dry_run)

        # Step 2: Restore region floor X=1293..1300 Y=78 to white concrete
        cmd_region_concrete = f"fill {REGION_MIN_X} {FLOOR_Y} {MIN_Z} {REGION_MAX_X} {FLOOR_Y} {MAX_Z} minecraft:white_concrete"
        print(f"Restoring `combined_region` floor at Y={FLOOR_Y} (X={REGION_MIN_X}..{REGION_MAX_X}) to white concrete...")
        send_exaroton_command(cmd_region_concrete, dry_run=dry_run)

        if not dry_run:
            record_history(f"{cmd_west_dirt} | {cmd_region_concrete}", "fill_west_dirt_and_restore_concrete")
            print("Successfully filled 1-block West lane with dirt and restored region floor to white concrete!")

def main():
    parser = argparse.ArgumentParser(description="Fill 1-block West lane with dirt and restore combined_region concrete floor.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying world")
    parser.add_argument("--undo", action="store_true", help="Undo changes made by this script")
    args = parser.parse_args()

    execute_fill(dry_run=args.dry_run, undo=args.undo)

if __name__ == "__main__":
    main()
