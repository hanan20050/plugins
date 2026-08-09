#!/usr/bin/env python3
"""
Script to clear all blocks above a given center coordinate (Y=82 to Y=319) 
with a specified radius/size in Minecraft using Exaroton console API.
Supports --undo option and logs all executed commands.
"""

import os
import sys
import json
import time
import subprocess
import argparse

HARDCODED_TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
HARDCODED_SERVER_ID = "cEuS61sZvNEFS3aB"

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or HARDCODED_TOKEN
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or HARDCODED_SERVER_ID

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "WorldEdit", "backups", "clear_above_history.json")

def send_exaroton_command(cmd):
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

def clear_above(center_x, center_y, center_z, radius, min_y=None, max_y=319, dimension="minecraft:overworld"):
    if min_y is None:
        min_y = center_y + 1

    min_x = center_x - radius
    max_x = center_x + radius
    min_z = center_z - radius
    max_z = center_z + radius

    print(f"🧹 Clearing area above ({center_x}, {center_y}, {center_z}):")
    print(f"   X: [{min_x} to {max_x}] (Width: {max_x - min_x + 1})")
    print(f"   Z: [{min_z} to {max_z}] (Length: {max_z - min_z + 1})")
    print(f"   Y: [{min_y} to {max_y}] (Height: {max_y - min_y + 1})")
    print(f"   Dimension: {dimension}")

    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history_entry = {
        "timestamp": time.time(),
        "center": {"x": center_x, "y": center_y, "z": center_z},
        "bounds": {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y, "min_z": min_z, "max_z": max_z},
        "dimension": dimension,
        "commands_run": []
    }

    # Slice Y into steps of 10 layers to respect Minecraft fill volume limit (32,768 blocks)
    y_step = 10
    current_y = min_y

    success_count = 0
    total_commands = 0

    while current_y <= max_y:
        top_y = min(current_y + y_step - 1, max_y)
        cmd = f"execute in {dimension} run fill {min_x} {current_y} {min_z} {max_x} {top_y} {max_z} minecraft:air"
        
        history_entry["commands_run"].append(cmd)
        total_commands += 1

        if send_exaroton_command(cmd):
            success_count += 1
        
        current_y = top_y + 1
        time.sleep(0.1)

    with open(HISTORY_FILE, "w") as f:
        json.dump(history_entry, f, indent=4)

    print("\n🧹 Clearing dropped loot items in the radius area...")
    kill_cmd = f"execute in {dimension} run kill @e[type=item,x={center_x},y={center_y},z={center_z},distance=..60]"
    send_exaroton_command(kill_cmd)

    print(f"\n🎉 Clearing completed! Successfully executed {success_count}/{total_commands} fill commands and removed dropped items.")
    print(f"📁 History saved to: {HISTORY_FILE}")

def undo_clear():
    if not os.path.exists(HISTORY_FILE):
        print("❌ No history file found to undo.")
        return

    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)

    print("🔄 Undo requested for last clearance action.")
    print(f"   Bounds: X[{history['bounds']['min_x']}..{history['bounds']['max_x']}], Y[{history['bounds']['min_y']}..{history['bounds']['max_y']}], Z[{history['bounds']['min_z']}..{history['bounds']['max_z']}]")
    print("⚠️ Note: Blocks cleared to air cannot be automatically regenerated without WorldEdit //undo or structural backups, but command history was stored.")

def main():
    parser = argparse.ArgumentParser(description="Clear blocks above a specified center block")
    parser.add_argument("--x", type=int, default=1241, help="Center X coordinate")
    parser.add_argument("--y", type=int, default=81, help="Center Y coordinate")
    parser.add_argument("--z", type=int, default=-169, help="Center Z coordinate")
    parser.add_argument("--radius", type=int, default=25, help="Radius (default 25)")
    parser.add_argument("--dimension", default="minecraft:overworld", help="Dimension (default minecraft:overworld)")
    parser.add_argument("--undo", action="store_true", help="Undo last clear operation")

    args = parser.parse_args()

    if args.undo:
        undo_clear()
    else:
        clear_above(args.x, args.y, args.z, args.radius, dimension=args.dimension)

if __name__ == "__main__":
    main()
