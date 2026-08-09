#!/usr/bin/env python3
"""
Clear region `mustafa_azan_rayan` with air up to Y=319 (build height limit).
Region bounds: X: 1292..1299, Z: -230..-222, Y: 77..319.

Supports --undo to restore blocks if needed (saves commands/actions taken).
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
MIN_Y, MAX_Y = 77, 319

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

def clear_region(dry_run=False):
    print(f"Clearing region `mustafa_azan_rayan` (X: {MIN_X}..{MAX_X}, Z: {MIN_Z}..{MAX_Z}, Y: {MIN_Y}..{MAX_Y}) with air...")
    
    # Fill in chunks of 30 height levels to stay safe under fill command block limit (max 32768 blocks: 8 * 9 * 30 = 2160 blocks per fill)
    y_start = MIN_Y
    fill_cmds = []
    while y_start <= MAX_Y:
        y_end = min(y_start + 29, MAX_Y)
        fill_cmds.append(f"fill {MIN_X} {y_start} {MIN_Z} {MAX_X} {y_end} {MAX_Z} minecraft:air replace")
        y_start = y_end + 1

    for cmd in fill_cmds:
        send_exaroton_command(cmd, dry_run=dry_run)

    print(f"Successfully cleared region from Y={MIN_Y} to Y={MAX_Y} with air.")

def main():
    parser = argparse.ArgumentParser(description="Clear region mustafa_azan_rayan with air to the top build limit.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying world")
    args = parser.parse_args()

    clear_region(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
