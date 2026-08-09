#!/usr/bin/env python3
"""
Manan End Farm Floor Outline Script (Leaves at Y=23 with Undo support)
"""

import os
import sys
import json
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

HISTORY_FILE = "WorldGuard/backups/manan_end_farm_outline_history.json"

REGION_BOUNDS = {
    "min_x": -56,
    "max_x": 43,
    "min_z": 185,
    "max_z": 284,
    "y": 23
}

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
            print(f"✅ Console Executed: {cmd}")
            return True
        else:
            print(f"❌ Command Error: {data.get('error')} | Output: {res.stdout}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def set_leaf_outline(leaf_type="oak_leaves"):
    min_x, max_x = REGION_BOUNDS["min_x"], REGION_BOUNDS["max_x"]
    min_z, max_z = REGION_BOUNDS["min_z"], REGION_BOUNDS["max_z"]
    y = REGION_BOUNDS["y"]
    dimension = "minecraft:the_end"
    mat = leaf_type if leaf_type.startswith("minecraft:") else f"minecraft:{leaf_type}"

    os.makedirs("WorldGuard/backups", exist_ok=True)
    history = {"bounds": REGION_BOUNDS, "material": mat, "dimension": dimension}
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

    print(f"🌿 Placing leaf outline ({mat}) for manan_end_farm in {dimension} at Y={y}...")

    # Execute in world_the_end dimension via execute in minecraft:the_end run fill ...
    cmds = [
        f"execute in {dimension} run fill {min_x} {y} {min_z} {max_x} {y} {min_z} {mat}",
        f"execute in {dimension} run fill {min_x} {y} {max_z} {max_x} {y} {max_z} {mat}",
        f"execute in {dimension} run fill {min_x} {y} {min_z} {min_x} {y} {max_z} {mat}",
        f"execute in {dimension} run fill {max_x} {y} {min_z} {max_x} {y} {max_z} {mat}"
    ]

    for c in cmds:
        send_exaroton_command(c)

    print("🎉 Leaf outline complete!")

def undo_leaf_outline():
    min_x, max_x = REGION_BOUNDS["min_x"], REGION_BOUNDS["max_x"]
    min_z, max_z = REGION_BOUNDS["min_z"], REGION_BOUNDS["max_z"]
    y = REGION_BOUNDS["y"]
    dimension = "minecraft:the_end"
    undo_mat = "minecraft:air"

    print(f"🔄 Reverting leaf outline for manan_end_farm at Y={y} in {dimension} to {undo_mat}...")
    cmds = [
        f"execute in {dimension} run fill {min_x} {y} {min_z} {max_x} {y} {min_z} {undo_mat}",
        f"execute in {dimension} run fill {min_x} {y} {max_z} {max_x} {y} {max_z} {undo_mat}",
        f"execute in {dimension} run fill {min_x} {y} {min_z} {min_x} {y} {max_z} {undo_mat}",
        f"execute in {dimension} run fill {max_x} {y} {min_z} {max_x} {y} {max_z} {undo_mat}"
    ]

    for c in cmds:
        send_exaroton_command(c)

    print("🎉 Leaf outline revert complete!")

def main():
    parser = argparse.ArgumentParser(description="Create leaf outline for manan_end_farm at Y=23 in the End")
    parser.add_argument("--material", default="oak_leaves", help="Leaf block type (default: oak_leaves)")
    parser.add_argument("--undo", action="store_true", help="Undo outline change and clear blocks")

    args = parser.parse_args()

    if args.undo:
        undo_leaf_outline()
    else:
        set_leaf_outline(args.material)

if __name__ == "__main__":
    main()
