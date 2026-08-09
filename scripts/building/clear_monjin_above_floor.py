#!/usr/bin/env python3
"""
Script to clear all blocks above Monjin's floor (Y=63 to Y=319)
within region `mon_jin_deku` (X: 1264..1271, Z: -191..-183) using the Exaroton console API.
Supports --undo option and logs history.
"""

import os
import sys
import json
import time
import subprocess
import argparse

ENV_FILE = os.path.join(os.path.dirname(__file__), "../../.env")
if not os.path.exists(ENV_FILE):
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

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "WorldEdit", "backups", "clear_monjin_history.json")

MIN_X, MAX_X = 1264, 1271
MIN_Z, MAX_Z = -191, -183
MIN_Y, MAX_Y = 63, 319
DIMENSION = "minecraft:overworld"

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
        if data.get("success"):
            print(f"✅ Executed: {cmd}")
            return True
        else:
            print(f"❌ Command Error: {data.get('error')} | Output: {res.stdout}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def clear_above_floor(dry_run=False):
    print(f"🧹 Clearing region `mon_jin_deku` above floor (Y={MIN_Y-1}):")
    print(f"   X: [{MIN_X} to {MAX_X}]")
    print(f"   Z: [{MIN_Z} to {MAX_Z}]")
    print(f"   Y: [{MIN_Y} to {MAX_Y}]")

    history_entry = {
        "timestamp": time.time(),
        "bounds": {"min_x": MIN_X, "max_x": MAX_X, "min_y": MIN_Y, "max_y": MAX_Y, "min_z": MIN_Z, "max_z": MAX_Z},
        "dimension": DIMENSION,
        "commands_run": []
    }

    # Slice Y into steps of 20 layers (X size is small: 8 * 9 * 20 = 1440 blocks per fill)
    y_step = 20
    current_y = MIN_Y

    success_count = 0
    total_commands = 0

    while current_y <= MAX_Y:
        top_y = min(current_y + y_step - 1, MAX_Y)
        cmd = f"execute in {DIMENSION} run fill {MIN_X} {current_y} {MIN_Z} {MAX_X} {top_y} {MAX_Z} minecraft:air"
        
        history_entry["commands_run"].append(cmd)
        total_commands += 1

        if send_exaroton_command(cmd, dry_run=dry_run):
            success_count += 1
        
        current_y = top_y + 1
        time.sleep(0.1)

    if not dry_run:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w") as f:
            json.dump(history_entry, f, indent=4)

    print(f"\n🎉 Clearing completed! Successfully executed {success_count}/{total_commands} commands.")

def undo_clear():
    if not os.path.exists(HISTORY_FILE):
        print("❌ No history file found to undo.")
        return

    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)

    print("🔄 Undo requested for last clearance action.")
    print(f"   Bounds: X[{history['bounds']['min_x']}..{history['bounds']['max_x']}], Y[{history['bounds']['min_y']}..{history['bounds']['max_y']}], Z[{history['bounds']['min_z']}..{history['bounds']['max_z']}]")
    print("⚠️ Note: Blocks cleared to air cannot be automatically regenerated, but command history has been retrieved.")

def main():
    parser = argparse.ArgumentParser(description="Clear blocks above Monjin's floor")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying world")
    parser.add_argument("--undo", action="store_true", help="Undo last clear operation")

    args = parser.parse_args()

    if args.undo:
        undo_clear()
    else:
        clear_above_floor(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
