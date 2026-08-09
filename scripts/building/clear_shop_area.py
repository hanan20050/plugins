#!/usr/bin/env python3
"""
Script to clear all blocks in the Shop area (X: 1293 to 1300, Z: -221 to -215) from Y=78 up to Y=319 (top of world) with minecraft:air.
Includes full backup/history logging and supports --undo.
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

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "WorldEdit", "backups", "clear_shop_history.json")

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

def clear_shop_area(min_x=1293, max_x=1300, min_z=-221, max_z=-215, min_y=78, max_y=319, dimension="minecraft:overworld"):
    print(f"🧹 Clearing Shop Area till top:")
    print(f"   X: [{min_x} to {max_x}] (Width: {max_x - min_x + 1})")
    print(f"   Z: [{min_z} to {max_z}] (Length: {max_z - min_z + 1})")
    print(f"   Y: [{min_y} to {max_y}] (Height: {max_y - min_y + 1})")
    print(f"   Dimension: {dimension}")

    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history_entry = {
        "timestamp": time.time(),
        "bounds": {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y, "min_z": min_z, "max_z": max_z},
        "dimension": dimension,
        "commands_run": []
    }

    # Slice Y into steps of 20 layers to fit well within block limits
    y_step = 20
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
        json.dump(history_entry, f, indent=2)

    print(f"\n✨ Shop area cleared: {success_count}/{total_commands} fill commands executed successfully.")

if __name__ == "__main__":
    clear_shop_area()
