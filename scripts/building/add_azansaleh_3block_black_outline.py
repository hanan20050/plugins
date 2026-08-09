#!/usr/bin/env python3
"""
Create a 3-block wide perimeter outline using Black Concrete on Azan Saleh's base floor (Y=62).

Region Bounds:
X: 1241 to 1255 (15 blocks wide)
Z: -219 to -191 (29 blocks long)
Y: 62

3-Block Perimeter Outline:
- North Border: Z: -219 to -217 across X: 1241..1255
- South Border: Z: -193 to -191 across X: 1241..1255
- West Border:  X: 1241 to 1243 across Z: -219..-191
- East Border:  X: 1253 to 1255 across Z: -219..-191

Supports --dry-run and --undo options.
"""

import os
import sys
import json
import subprocess
import argparse

BACKUP_FILE = "azansaleh_3block_outline_history.json"

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

def apply_3block_outline(dry_run=False):
    print("Applying 3-block wide Black Concrete perimeter outline on Azan's floor (Y=62)...")
    
    cmds = [
        f"fill {MIN_X} {Y} -219 {MAX_X} {Y} -217 minecraft:black_concrete", # North 3-block border
        f"fill {MIN_X} {Y} -193 {MAX_X} {Y} -191 minecraft:black_concrete", # South 3-block border
        f"fill 1241 {Y} {MIN_Z} 1243 {Y} {MAX_Z} minecraft:black_concrete", # West 3-block border
        f"fill 1253 {Y} {MIN_Z} 1255 {Y} {MAX_Z} minecraft:black_concrete", # East 3-block border
    ]
    
    history = []
    for cmd in cmds:
        print(f"Executing: {cmd}")
        success = send_exaroton_command(cmd, dry_run=dry_run)
        if success:
            history.append(cmd)

    if not dry_run:
        with open(BACKUP_FILE, "w") as f:
            json.dump({"applied_commands": history}, f, indent=2)
        print(f"3-block outline created successfully! Saved history to {BACKUP_FILE}")

def undo(dry_run=False):
    print("Undoing 3-block outline (restoring floor to 2-color concrete)...")
    cmd1 = f"fill {MIN_X} {Y} -219 {MAX_X} {Y} -205 minecraft:white_concrete"
    cmd2 = f"fill {MIN_X} {Y} -204 {MAX_X} {Y} -191 minecraft:cyan_concrete"
    send_exaroton_command(cmd1, dry_run=dry_run)
    send_exaroton_command(cmd2, dry_run=dry_run)
    print("Floor outline restored.")

def main():
    parser = argparse.ArgumentParser(description="Create 3-block wide Black Concrete outline on Azan's floor")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--undo", action="store_true", help="Undo outline creation")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        apply_3block_outline(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
