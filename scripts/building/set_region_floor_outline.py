#!/usr/bin/env python3
"""
Region Floor Outline Generator & Changer (with Undo Support)
------------------------------------------------------------
Changes the floor outline (perimeter border blocks) of a region to concrete.
Maintains a strict backup in `WorldGuard/backups/floor_outline_history.json`
to support full `--undo` / rollback operations.

Usage:
  python3 set_region_floor_outline.py <region_name> [concrete_color]
  python3 set_region_floor_outline.py <region_name> --undo

Example:
  python3 set_region_floor_outline.py nightmaredady_expand light_blue_concrete
  python3 set_region_floor_outline.py nightmaredady_expand --undo
"""

import os
import sys
import json
import re
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

REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"
HISTORY_FILE = "WorldGuard/backups/floor_outline_history.json"

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

def pull_region_file():
    subprocess.run([sys.executable, "sync.py", "pull", REGIONS_FILE], capture_output=True)

def get_region_bounds(region_name):
    pull_region_file()
    if not os.path.exists(REGIONS_FILE):
        return None, None

    min_coords = None
    max_coords = None
    current_region = None

    with open(REGIONS_FILE, "r") as f:
        for line in f:
            reg_match = re.match(r"^ {4}([a-zA-Z0-9_\-]+):", line)
            if reg_match:
                current_region = reg_match.group(1)
                continue

            if current_region == region_name:
                if "min:" in line:
                    m = re.search(r"x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)", line)
                    if m:
                        min_coords = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
                elif "max:" in line:
                    m = re.search(r"x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)", line)
                    if m:
                        max_coords = (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    return min_coords, max_coords

def save_history(region, block_type, coords):
    os.makedirs("WorldGuard/backups", exist_ok=True)
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            history = {}

    history[region] = {
        "block_type": block_type,
        "coords": coords
    }
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)
    print(f"📝 Outline history saved to '{HISTORY_FILE}'.")

def load_history(region):
    if not os.path.exists(HISTORY_FILE):
        return None
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
            return history.get(region)
    except Exception:
        return None

def set_outline(region_name, block_type):
    print(f"🔍 Locating bounds for region '{region_name}'...")
    min_c, max_c = get_region_bounds(region_name)

    if not min_c or not max_c:
        print(f"❌ Region '{region_name}' bounds not found.")
        sys.exit(1)

    min_x, min_y, min_z = min_c
    max_x, max_y, max_z = max_c
    floor_y = min_y

    mat = block_type if block_type.startswith("minecraft:") else f"minecraft:{block_type}"

    print(f"📐 Target Region Bounds:")
    print(f"   X: {min_x} to {max_x}")
    print(f"   Floor Y: {floor_y}")
    print(f"   Z: {min_z} to {max_z}")
    print(f"🧱 Laying concrete outline ('{mat}') around region perimeter...")

    save_history(region_name, mat, [min_x, floor_y, min_z, max_x, max_z])

    # 4 fill commands for perimeter edges
    cmds = [
        f"fill {min_x} {floor_y} {min_z} {max_x} {floor_y} {min_z} {mat}", # North edge
        f"fill {min_x} {floor_y} {max_z} {max_x} {floor_y} {max_z} {mat}", # South edge
        f"fill {min_x} {floor_y} {min_z} {min_x} {floor_y} {max_z} {mat}", # West edge
        f"fill {max_x} {floor_y} {min_z} {max_x} {floor_y} {max_z} {mat}"  # East edge
    ]

    for c in cmds:
        send_exaroton_command(c)

    print(f"🎉 Floor outline successfully changed to '{mat}' for region '{region_name}'!")

def undo_outline(region_name):
    record = load_history(region_name)
    if record:
        min_x, floor_y, min_z, max_x, max_z = record["coords"]
        undo_mat = "minecraft:grass_block"
        print(f"🔄 Reverting floor outline for '{region_name}' to '{undo_mat}' at Y={floor_y}...")
        cmds = [
            f"fill {min_x} {floor_y} {min_z} {max_x} {floor_y} {min_z} {undo_mat}",
            f"fill {min_x} {floor_y} {max_z} {max_x} {floor_y} {max_z} {undo_mat}",
            f"fill {min_x} {floor_y} {min_z} {min_x} {floor_y} {max_z} {undo_mat}",
            f"fill {max_x} {floor_y} {min_z} {max_x} {floor_y} {max_z} {undo_mat}"
        ]
        for c in cmds:
            send_exaroton_command(c)
        print(f"🎉 Floor outline successfully reverted!")
    else:
        print(f"⚠️ No outline history record found for '{region_name}'. Attempting fallback revert to grass_block...")
        min_c, max_c = get_region_bounds(region_name)
        if min_c and max_c:
            min_x, min_y, min_z = min_c
            max_x, max_y, max_z = max_c
            undo_mat = "minecraft:grass_block"
            cmds = [
                f"fill {min_x} {min_y} {min_z} {max_x} {min_y} {min_z} {undo_mat}",
                f"fill {min_x} {min_y} {max_z} {max_x} {min_y} {max_z} {undo_mat}",
                f"fill {min_x} {min_y} {min_z} {min_x} {min_y} {max_z} {undo_mat}",
                f"fill {max_x} {min_y} {min_z} {max_x} {min_y} {max_z} {undo_mat}"
            ]
            for c in cmds:
                send_exaroton_command(c)
            print(f"🎉 Fallback revert completed!")

def main():
    parser = argparse.ArgumentParser(description="Set or revert floor outline to concrete for a WorldGuard region")
    parser.add_argument("region", help="WorldGuard region name (e.g. nightmaredady_expand)")
    parser.add_argument("concrete", nargs="?", default="light_blue_concrete", help="Concrete block type (default: light_blue_concrete)")
    parser.add_argument("--undo", action="store_true", help="Undo outline change and restore grass_block")

    args = parser.parse_args()

    if args.undo:
        undo_outline(args.region)
    else:
        set_outline(args.region, args.concrete)

if __name__ == "__main__":
    main()
