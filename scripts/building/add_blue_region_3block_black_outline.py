#!/usr/bin/env python3
"""
Create a 3-block wide Black Concrete perimeter outline ONLY for the Blue Concrete region in Azan's area.

Blue Region Bounds:
X: 1248 to 1255 (8 blocks wide)
Z: -219 to -205 (15 blocks long)
Y: 62

3-Block Perimeter Outline:
- North Border: Z: -219 to -217 across X: 1248..1255
- South Border: Z: -207 to -205 across X: 1248..1255
- West Border:  X: 1248 to 1250 across Z: -219..-205
- East Border:  X: 1253 to 1255 across Z: -219..-205

Supports --block, --dry-run, and --undo options.
"""

import os
import sys
import json
import subprocess
import argparse

BACKUP_FILE = "blue_region_3block_outline_history.json"

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

MIN_X, MAX_X = 1248, 1255
MIN_Z, MAX_Z = -219, -205
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

def apply_blue_region_outline(outline_block="minecraft:black_concrete", dry_run=False):
    if not outline_block.startswith("minecraft:"):
        outline_block = f"minecraft:{outline_block}"

    print(f"Applying 3-block wide {outline_block} perimeter outline ONLY for Blue Region at Y={Y}...")
    
    cmds = [
        f"fill {MIN_X} {Y} -219 {MAX_X} {Y} -217 {outline_block}", # North 3-block border
        f"fill {MIN_X} {Y} -207 {MAX_X} {Y} -205 {outline_block}", # South 3-block border
        f"fill 1248 {Y} {MIN_Z} 1250 {Y} {MAX_Z} {outline_block}", # West 3-block border
        f"fill 1253 {Y} {MIN_Z} 1255 {Y} {MAX_Z} {outline_block}", # East 3-block border
    ]
    
    history = []
    for cmd in cmds:
        print(f"Executing: {cmd}")
        success = send_exaroton_command(cmd, dry_run=dry_run)
        if success:
            history.append(cmd)

    if not dry_run:
        with open(BACKUP_FILE, "w") as f:
            json.dump({"applied_commands": history, "block": outline_block}, f, indent=2)
        print(f"Blue region 3-block outline created successfully! Saved history to {BACKUP_FILE}")

def undo(dry_run=False):
    print("Undoing 3-block outline for Blue Region (restoring to white_concrete)...")
    cmd = f"fill {MIN_X} {Y} {MIN_Z} {MAX_X} {Y} {MAX_Z} minecraft:white_concrete"
    send_exaroton_command(cmd, dry_run=dry_run)
    print("Blue region floor restored.")

def main():
    parser = argparse.ArgumentParser(description="Create 3-block wide outline ONLY for Blue Region")
    parser.add_argument("--block", default="minecraft:black_concrete", help="Outline block material")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--undo", action="store_true", help="Undo outline creation")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        apply_blue_region_outline(outline_block=args.block, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
