#!/usr/bin/env python3
"""
Replace floor layer of `mustafa_azan_rayan` region with concrete.
Region bounds: X: 1292..1299, Z: -230..-222, Y: 77.

Supports material option (default: minecraft:white_concrete), dry-run, and undo.
"""

import os
import sys
import json
import subprocess
import argparse

# Load credentials
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
FLOOR_Y = 77

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

def replace_floor_concrete(material="minecraft:white_concrete", dry_run=False, undo=False):
    if not material.startswith("minecraft:"):
        material = f"minecraft:{material}"

    if undo:
        # Revert floor to dirt/air (dirt was previous floor material)
        cmd = f"fill {MIN_X} {FLOOR_Y} {MIN_Z} {MAX_X} {FLOOR_Y} {MAX_Z} minecraft:dirt"
        print(f"Reverting floor level Y={FLOOR_Y} of `mustafa_azan_rayan` to dirt...")
    else:
        cmd = f"fill {MIN_X} {FLOOR_Y} {MIN_Z} {MAX_X} {FLOOR_Y} {MAX_Z} {material}"
        print(f"Replacing floor level Y={FLOOR_Y} of `mustafa_azan_rayan` (X: {MIN_X}..{MAX_X}, Z: {MIN_Z}..{MAX_Z}) with {material}...")

    success = send_exaroton_command(cmd, dry_run=dry_run)
    if success:
        if undo:
            print("Successfully reverted floor level to dirt.")
        else:
            print(f"Successfully replaced floor level with {material}.")
    return success

def main():
    parser = argparse.ArgumentParser(description="Replace floor of mustafa_azan_rayan region with concrete.")
    parser.add_argument("--material", default="minecraft:white_concrete", help="Concrete block type (default: minecraft:white_concrete)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying world")
    parser.add_argument("--undo", action="store_true", help="Undo concrete floor by setting level back to dirt")
    args = parser.parse_args()

    replace_floor_concrete(material=args.material, dry_run=args.dry_run, undo=args.undo)

if __name__ == "__main__":
    main()
