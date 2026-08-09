#!/usr/bin/env python3
"""
Extend Monjin's region (mon_jin_deku) to include adjacent selection,
set floor to Y=62 and height to 15 blocks (Y=62 to Y=76).
Updates WorldGuard region bounds locally, pushes to server, reloads WorldGuard,
and updates player_regions_registry.json.
Provides full Undo support.
"""

import os
import sys
import json
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

WORLD_NAME = "world"
REGION_ID = "mon_jin_deku"
REGISTRY_FILE = "player_regions_registry.json"
REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"
BACKUP_FILE = f"WorldGuard/backups/{REGION_ID}_extend_backup.json"

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
            print(f"✅ Console Command: {cmd}")
            return True
        else:
            print(f"❌ Command Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Exception parsing API response: {e}")
        return False

def pull_file(filepath):
    print(f"🔄 Pulling latest {filepath}...")
    res = subprocess.run([sys.executable, "sync.py", "pull", filepath, "--force"], capture_output=True, text=True)
    print(res.stdout.strip())

def push_file(filepath):
    print(f"🔄 Pushing updated {filepath}...")
    res = subprocess.run([sys.executable, "sync.py", "push", filepath, "-y"], capture_output=True, text=True)
    print(res.stdout.strip())

def main():
    parser = argparse.ArgumentParser(description="Extend Monjin's region with undo support")
    parser.add_argument("--undo", action="store_true", help="Undo extension and revert to backup bounds")
    args = parser.parse_args()

    pull_file(REGISTRY_FILE)
    pull_file(REGIONS_FILE)

    if not os.path.exists(REGISTRY_FILE):
        print(f"❌ Registry file {REGISTRY_FILE} not found!")
        sys.exit(1)
    if not os.path.exists(REGIONS_FILE):
        print(f"❌ WorldGuard regions file {REGIONS_FILE} not found!")
        sys.exit(1)

    with open(REGISTRY_FILE, "r") as f:
        registry_data = json.load(f)

    if args.undo:
        if not os.path.exists(BACKUP_FILE):
            print(f"❌ Backup file {BACKUP_FILE} not found! Cannot undo.")
            sys.exit(1)

        with open(BACKUP_FILE, "r") as f:
            backup_data = json.load(f)

        print("🔄 Reverting WorldGuard region yml to backup bounds...")
        with open(REGIONS_FILE, "r") as f:
            regions_content = f.read()

        # Revert min and max bounds for mon_jin_deku
        old_min_line = "min: {x: 1257, y: 62, z: -191}"
        new_min_line = "min: {x: 1264, y: 62, z: -191}"
        old_max_line = "max: {x: 1271, y: 76, z: -183}"
        new_max_line = "max: {x: 1271, y: 68, z: -183}"

        regions_content = regions_content.replace(old_min_line, new_min_line)
        regions_content = regions_content.replace(old_max_line, new_max_line)

        with open(REGIONS_FILE, "w") as f:
            f.write(regions_content)

        push_file(REGIONS_FILE)
        send_exaroton_command("rg reload")

        # Restore registry
        registry_data["regions"][REGION_ID] = backup_data["registry_entry"]
        with open(REGISTRY_FILE, "w") as f:
            json.dump(registry_data, f, indent=4)
        push_file(REGISTRY_FILE)
        print("🎉 Successfully reverted Monjin's region bounds and registry entry!")
        return

    # Original region entry backup
    if REGION_ID not in registry_data["regions"]:
        print(f"❌ Region {REGION_ID} not found in registry!")
        sys.exit(1)

    original_entry = registry_data["regions"][REGION_ID]

    # Save backup details
    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    backup_data = {
        "min": {
            "x": 1264,
            "y": 62,
            "z": -191
        },
        "max": {
            "x": 1271,
            "y": 68,
            "z": -183
        },
        "registry_entry": original_entry
    }
    with open(BACKUP_FILE, "w") as f:
        json.dump(backup_data, f, indent=4)
    print(f"💾 Backup saved to {BACKUP_FILE}")

    # Redefine on server by modifying regions.yml directly
    new_min_x, new_max_x = 1257, 1271
    new_min_y, new_max_y = 62, 76
    new_min_z, new_max_z = -191, -183

    print(f"📐 Extending region '{REGION_ID}' locally:")
    print(f"   X: {new_min_x}..{new_max_x}")
    print(f"   Y: {new_min_y}..{new_max_y} (Height: 15)")
    print(f"   Z: {new_min_z}..{new_max_z}")

    with open(REGIONS_FILE, "r") as f:
        regions_content = f.read()

    old_min_line = "min: {x: 1264, y: 62, z: -191}"
    new_min_line = f"min: {{x: {new_min_x}, y: {new_min_y}, z: {new_min_z}}}"
    old_max_line = "max: {x: 1271, y: 68, z: -183}"
    new_max_line = f"max: {{x: {new_max_x}, y: {new_max_y}, z: {new_max_z}}}"

    if old_min_line not in regions_content or old_max_line not in regions_content:
        print("❌ Error: Could not find original mon_jin_deku bounds in regions.yml!")
        sys.exit(1)

    regions_content = regions_content.replace(old_min_line, new_min_line)
    regions_content = regions_content.replace(old_max_line, new_max_line)

    with open(REGIONS_FILE, "w") as f:
        f.write(regions_content)

    push_file(REGIONS_FILE)
    send_exaroton_command("rg reload")

    # Update registry
    registry_data["regions"][REGION_ID] = {
        "min_corner": {
            "x": new_min_x,
            "y": new_min_y,
            "z": new_min_z
        },
        "max_corner": {
            "x": new_max_x,
            "y": new_max_y,
            "z": new_max_z
        },
        "dimensions": {
            "width_x": (new_max_x - new_min_x) + 1,
            "length_z": (new_max_z - new_min_z) + 1,
            "height_y": (new_max_y - new_min_y) + 1
        },
        "surface_area_sq_blocks": ((new_max_x - new_min_x) + 1) * ((new_max_z - new_min_z) + 1),
        "size_category": "Starter / Base Plot",
        "floor_y_level": new_min_y,
        "raw_uuids": original_entry.get("raw_uuids", "00000000-0000-0000-0009-01fa2d270090")
    }

    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry_data, f, indent=4)
    push_file(REGISTRY_FILE)
    print("🎉 Successfully extended Monjin's region bounds and updated registry!")

if __name__ == "__main__":
    main()
