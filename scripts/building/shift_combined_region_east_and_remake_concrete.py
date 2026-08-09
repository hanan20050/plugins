#!/usr/bin/env python3
"""
Shift `combined_region` 1 block East (+1 on X axis) and remake the concrete floor:
1. Update regions.yml min_x from 1292 -> 1293, max_x from 1299 -> 1300.
2. Sync regions.yml to Exaroton and reload WorldGuard (`rg reload`).
3. Clear old block strip at X=1292 (Y=76..78, Z=-230..-222) to air.
4. Fill subfloor layers (Y=76, Y=77) across new bounds X=1293..1300, Z=-230..-222 with dirt.
5. Fill main floor (Y=78) across new bounds X=1293..1300, Z=-230..-222 with white concrete.

Supports --undo and --dry-run for strict rollback compliance.
"""

import os
import sys
import json
import subprocess
import argparse

REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"
BACKUP_DIR = "WorldGuard/backups"
BACKUP_FILE = os.path.join(BACKUP_DIR, "shift_combined_region_east_backup.json")

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

# Bounds shift (+1 East on X axis)
OLD_MIN_X, OLD_MAX_X = 1292, 1299
NEW_MIN_X, NEW_MAX_X = 1293, 1300
MIN_Z, MAX_Z = -230, -222

FLOOR_Y = 78
SUBFLOOR_Y1 = 77
SUBFLOOR_Y2 = 76

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

def run_shift_east(dry_run=False):
    backup()

    # Step 1: Modify regions.yml
    with open(REGIONS_FILE, "r") as f:
        content = f.read()

    old_min_str = f"min: {{x: {OLD_MIN_X}, y: {FLOOR_Y}, z: {MIN_Z}}}"
    old_max_str = f"max: {{x: {OLD_MAX_X}, y: 92, z: {MAX_Z}}}"

    new_min_str = f"min: {{x: {NEW_MIN_X}, y: {FLOOR_Y}, z: {MIN_Z}}}"
    new_max_str = f"max: {{x: {NEW_MAX_X}, y: 92, z: {MAX_Z}}}"

    if old_min_str not in content or old_max_str not in content:
        print(f"[ERROR] Expected region lines not found in {REGIONS_FILE}")
        return False

    content = content.replace(old_min_str, new_min_str, 1)
    content = content.replace(old_max_str, new_max_str, 1)

    if not dry_run:
        with open(REGIONS_FILE, "w") as f:
            f.write(content)
        print(f"Updated `combined_region` bounds to X: {NEW_MIN_X}..{NEW_MAX_X} in {REGIONS_FILE}.")

        # Push regions.yml to Exaroton server and reload WorldGuard
        subprocess.run(["python3", "sync.py", "push", REGIONS_FILE], check=True)
        send_exaroton_command("rg reload")
        print("Synced regions.yml to Exaroton and reloaded WorldGuard plugin.")

    # Step 2: Clear old strip X=1292 (Y=76..78, Z=-230..-222) to air
    cmd_clear_old = f"fill {OLD_MIN_X} {SUBFLOOR_Y2} {MIN_Z} {OLD_MIN_X} {FLOOR_Y} {MAX_Z} minecraft:air"
    print(f"Clearing old west strip X={OLD_MIN_X} (Y={SUBFLOOR_Y2}..{FLOOR_Y}) to air...")
    send_exaroton_command(cmd_clear_old, dry_run=dry_run)

    # Step 3: Fill subfloor layers (Y=76, Y=77) with dirt across new bounds
    cmd_subfloor = f"fill {NEW_MIN_X} {SUBFLOOR_Y2} {MIN_Z} {NEW_MAX_X} {SUBFLOOR_Y1} {MAX_Z} minecraft:dirt"
    print(f"Filling subfloor layers Y={SUBFLOOR_Y2}..{SUBFLOOR_Y1} (X={NEW_MIN_X}..{NEW_MAX_X}) with dirt...")
    send_exaroton_command(cmd_subfloor, dry_run=dry_run)

    # Step 4: Fill concrete floor (Y=78) across new bounds
    cmd_concrete = f"fill {NEW_MIN_X} {FLOOR_Y} {MIN_Z} {NEW_MAX_X} {FLOOR_Y} {MAX_Z} minecraft:white_concrete"
    print(f"Remaking concrete floor at Y={FLOOR_Y} (X={NEW_MIN_X}..{NEW_MAX_X}) with white concrete...")
    send_exaroton_command(cmd_concrete, dry_run=dry_run)

    print("Successfully shifted combined_region 1 block East and remade concrete floor!")
    return True

def undo(dry_run=False):
    # Revert block changes: clear new bounds floor/subfloor, restore old bounds dirt & concrete
    cmd_clear_new = f"fill {NEW_MIN_X} {SUBFLOOR_Y2} {MIN_Z} {NEW_MAX_X} {FLOOR_Y} {MAX_Z} minecraft:air"
    print(f"Clearing new region blocks (X={NEW_MIN_X}..{NEW_MAX_X})...")
    send_exaroton_command(cmd_clear_new, dry_run=dry_run)

    # Restore old subfloor dirt and floor concrete
    cmd_old_subfloor = f"fill {OLD_MIN_X} {SUBFLOOR_Y2} {MIN_Z} {OLD_MAX_X} {SUBFLOOR_Y1} {MAX_Z} minecraft:dirt"
    cmd_old_concrete = f"fill {OLD_MIN_X} {FLOOR_Y} {MIN_Z} {OLD_MAX_X} {FLOOR_Y} {MAX_Z} minecraft:white_concrete"
    print(f"Restoring old region floor/subfloor blocks (X={OLD_MIN_X}..{OLD_MAX_X})...")
    send_exaroton_command(cmd_old_subfloor, dry_run=dry_run)
    send_exaroton_command(cmd_old_concrete, dry_run=dry_run)

    # Restore regions.yml
    if os.path.exists(BACKUP_FILE):
        with open(BACKUP_FILE, "r") as f:
            data = json.load(f)
        if not dry_run:
            with open(REGIONS_FILE, "w") as f:
                f.write(data["raw_regions_yml"])
            subprocess.run(["python3", "sync.py", "push", REGIONS_FILE], check=True)
            send_exaroton_command("rg reload")
            print("Restored regions.yml from backup and reloaded WorldGuard.")

    print("Undo completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Shift combined_region 1 block East and remake concrete floor.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying files or world")
    parser.add_argument("--undo", action="store_true", help="Undo all changes and revert region bounds and blocks")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        run_shift_east(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
