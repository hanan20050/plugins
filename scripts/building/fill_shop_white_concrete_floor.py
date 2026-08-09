#!/usr/bin/env python3
"""
Fill floor of `shop` region with white concrete.
Region bounds: X: 1293..1300, Z: -221..-215, Y: 78.

Supports undo and dry-run modes.
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

MIN_X, MAX_X = 1293, 1300
MIN_Z, MAX_Z = -221, -215
FLOOR_Y = 78

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

def fill_shop_floor(dry_run=False, undo=False):
    if undo:
        cmd = f"fill {MIN_X} {FLOOR_Y} {MIN_Z} {MAX_X} {FLOOR_Y} {MAX_Z} minecraft:air"
        print(f"Reverting floor level Y={FLOOR_Y} of `shop` region to air...")
    else:
        cmd = f"fill {MIN_X} {FLOOR_Y} {MIN_Z} {MAX_X} {FLOOR_Y} {MAX_Z} minecraft:white_concrete"
        print(f"Filling floor level Y={FLOOR_Y} of `shop` region (X: {MIN_X}..{MAX_X}, Z: {MIN_Z}..{MAX_Z}) with white concrete...")

    success = send_exaroton_command(cmd, dry_run=dry_run)
    if success:
        if undo:
            print("Successfully reverted shop floor to air.")
        else:
            print("Successfully filled shop floor with white concrete.")

def main():
    parser = argparse.ArgumentParser(description="Fill floor of shop region with white concrete.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying world")
    parser.add_argument("--undo", action="store_true", help="Undo white concrete floor by setting level back to air")
    args = parser.parse_args()

    fill_shop_floor(dry_run=args.dry_run, undo=args.undo)

if __name__ == "__main__":
    main()
