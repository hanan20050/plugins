#!/usr/bin/env python3
"""
Upgrade Mustafa, Rayan, and Azan's shared region (`mustafa_azan_rayan`):
1. Redefine region floor 1 level above (Y=78 instead of Y=77).
2. Fill old floor level (Y=77) 1 block below with dirt.
3. Fill new region floor (Y=78) with white concrete.

Region bounds: X: 1292..1299, Z: -230..-222.
Supports --dry-run and --undo options.
"""

import os
import sys
import json
import subprocess
import argparse

REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"
BACKUP_DIR = "WorldGuard/backups"
BACKUP_FILE = os.path.join(BACKUP_DIR, "mustafa_rayan_azan_floor_upgrade_backup.json")

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
OLD_FLOOR_Y = 77
NEW_FLOOR_Y = 78

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

def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if os.path.exists(REGIONS_FILE):
        with open(REGIONS_FILE, "r") as f:
            content = f.read()
        with open(BACKUP_FILE, "w") as f:
            json.dump({"raw_regions_yml": content}, f, indent=2)
        print(f"Backed up {REGIONS_FILE} to {BACKUP_FILE}")

def run_upgrade(material="minecraft:white_concrete", dry_run=False):
    if not material.startswith("minecraft:"):
        material = f"minecraft:{material}"

    backup()

    # Step 1: Redefine region floor to Y=78 in regions.yml
    with open(REGIONS_FILE, "r") as f:
        content = f.read()

    old_min_line = "min: {x: 1292, y: 77, z: -230}"
    new_min_line = "min: {x: 1292, y: 78, z: -230}"

    if old_min_line in content:
        content = content.replace(old_min_line, new_min_line)
        if not dry_run:
            with open(REGIONS_FILE, "w") as f:
                f.write(content)
            print("Updated `mustafa_azan_rayan` region floor boundary to Y=78 in regions.yml.")
            # Sync to server and reload WorldGuard
            subprocess.run(["python3", "sync.py", "push", REGIONS_FILE], check=True)
            send_exaroton_command("rg reload", dry_run=False)
            print("Pushed regions.yml to Exaroton and reloaded WorldGuard.")
    else:
        print(f"[WARNING] Target min line '{old_min_line}' not found in {REGIONS_FILE}.")

    # Step 2: Fill old floor level (Y=77) with dirt
    cmd_dirt = f"fill {MIN_X} {OLD_FLOOR_Y} {MIN_Z} {MAX_X} {OLD_FLOOR_Y} {MAX_Z} minecraft:dirt"
    print(f"Filling old floor Y={OLD_FLOOR_Y} with dirt...")
    send_exaroton_command(cmd_dirt, dry_run=dry_run)

    # Step 3: Fill new floor level (Y=78) with concrete
    cmd_concrete = f"fill {MIN_X} {NEW_FLOOR_Y} {MIN_Z} {MAX_X} {NEW_FLOOR_Y} {MAX_Z} {material}"
    print(f"Filling new floor Y={NEW_FLOOR_Y} with {material}...")
    send_exaroton_command(cmd_concrete, dry_run=dry_run)

    print("Successfully completed floor upgrade for `mustafa_azan_rayan`!")

def undo(dry_run=False):
    # Revert block fills
    cmd_undo_concrete = f"fill {MIN_X} {NEW_FLOOR_Y} {MIN_Z} {MAX_X} {NEW_FLOOR_Y} {MAX_Z} minecraft:air"
    cmd_undo_dirt = f"fill {MIN_X} {OLD_FLOOR_Y} {MIN_Z} {MAX_X} {OLD_FLOOR_Y} {MAX_Z} minecraft:air"
    
    print(f"Reverting new floor Y={NEW_FLOOR_Y} to air...")
    send_exaroton_command(cmd_undo_concrete, dry_run=dry_run)

    print(f"Reverting old floor Y={OLD_FLOOR_Y} to air...")
    send_exaroton_command(cmd_undo_dirt, dry_run=dry_run)

    # Restore regions.yml
    if os.path.exists(BACKUP_FILE):
        with open(BACKUP_FILE, "r") as f:
            data = json.load(f)
        if not dry_run:
            with open(REGIONS_FILE, "w") as f:
                f.write(data["raw_regions_yml"])
            subprocess.run(["python3", "sync.py", "push", REGIONS_FILE], check=True)
            send_exaroton_command("rg reload", dry_run=False)
            print("Restored regions.yml from backup and reloaded WorldGuard.")
    print("Undo completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Upgrade floor for mustafa_azan_rayan region.")
    parser.add_argument("--material", default="minecraft:white_concrete", help="Concrete block type (default: minecraft:white_concrete)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying world")
    parser.add_argument("--undo", action="store_true", help="Undo all changes made by this script")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        run_upgrade(material=args.material, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
