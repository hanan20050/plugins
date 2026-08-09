#!/usr/bin/env python3
"""
Mark the outline for the base floor of the blue marked region in Azan's area.

Blue Region Bounds:
X: 1248 to 1255
Z: -219 to -205
Y: 62

Perimeter outline lines:
- North: fill 1248 62 -219 1255 62 -219 <outline_block>
- South: fill 1248 62 -205 1255 62 -205 <outline_block>
- West:  fill 1248 62 -219 1248 62 -205 <outline_block>
- East:  fill 1255 62 -219 1255 62 -205 <outline_block>

Supports --outline-block, --dry-run, and --undo options.
"""

import os
import sys
import json
import subprocess
import argparse

BACKUP_FILE = "azan_blue_region_outline_history.json"

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

def apply_outline(outline_block="minecraft:sea_lantern", dry_run=False):
    if not outline_block.startswith("minecraft:"):
        outline_block = f"minecraft:{outline_block}"

    print(f"Marking perimeter outline for Blue Region at Y={Y} using {outline_block}...")
    
    cmds = [
        f"fill {MIN_X} {Y} {MIN_Z} {MAX_X} {Y} {MIN_Z} {outline_block}", # North
        f"fill {MIN_X} {Y} {MAX_Z} {MAX_X} {Y} {MAX_Z} {outline_block}", # South
        f"fill {MIN_X} {Y} {MIN_Z} {MIN_X} {Y} {MAX_Z} {outline_block}", # West
        f"fill {MAX_X} {Y} {MIN_Z} {MAX_X} {Y} {MAX_Z} {outline_block}", # East
    ]
    
    history = []
    for cmd in cmds:
        print(f"Executing: {cmd}")
        success = send_exaroton_command(cmd, dry_run=dry_run)
        if success:
            history.append(cmd)

    if not dry_run:
        with open(BACKUP_FILE, "w") as f:
            json.dump({"applied_commands": history, "outline_block": outline_block}, f, indent=2)
        print(f"Saved outline history to {BACKUP_FILE}")

def undo(dry_run=False):
    print(f"Undoing outline (restoring perimeter back to minecraft:blue_concrete)...")
    cmds = [
        f"fill {MIN_X} {Y} {MIN_Z} {MAX_X} {Y} {MIN_Z} minecraft:blue_concrete",
        f"fill {MIN_X} {Y} {MAX_Z} {MAX_X} {Y} {MAX_Z} minecraft:blue_concrete",
        f"fill {MIN_X} {Y} {MIN_Z} {MIN_X} {Y} {MAX_Z} minecraft:blue_concrete",
        f"fill {MAX_X} {Y} {MIN_Z} {MAX_X} {Y} {MAX_Z} minecraft:blue_concrete",
    ]
    for cmd in cmds:
        send_exaroton_command(cmd, dry_run=dry_run)
    print("Blue region perimeter restored to minecraft:blue_concrete.")

def main():
    parser = argparse.ArgumentParser(description="Mark outline for blue region in Azan area")
    parser.add_argument("--block", default="minecraft:sea_lantern", help="Outline block material")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--undo", action="store_true", help="Undo outline changes")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        apply_outline(outline_block=args.block, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
