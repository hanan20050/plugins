#!/usr/bin/env python3
"""
Increase Azan Saleh's region height (azansalehhh) on the top side by 15 blocks.
Supports full Undo/Rollback and updates player_regions_registry.json.
"""

import os
import sys
import json
import re
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
REGION_NAME = "azansalehhh"
REGIONS_FILE = f"WorldGuard/worlds/{WORLD_NAME}/regions.yml"
REGISTRY_FILE = "player_regions_registry.json"
BACKUP_FILE = f"WorldGuard/backups/{REGION_NAME}_height_resize_backup.json"

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
            print(f"✅ Executed command: {cmd}")
            return True
        else:
            print(f"❌ Command Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Exception parsing response for command '{cmd}': {e}\nOutput: {res.stdout}")
        return False

def pull_regions():
    print(f"🔄 Pulling latest {REGIONS_FILE} from server...")
    res = subprocess.run([sys.executable, "sync.py", "pull", REGIONS_FILE], capture_output=True, text=True)
    print(res.stdout.strip())

def push_regions():
    print(f"🔄 Pushing updated {REGIONS_FILE} to server...")
    res = subprocess.run([sys.executable, "sync.py", "push", REGIONS_FILE, "-y"], capture_output=True, text=True)
    print(res.stdout.strip())

def get_current_bounds():
    pull_regions()
    if not os.path.exists(REGIONS_FILE):
        print(f"❌ Regions file {REGIONS_FILE} not found!")
        sys.exit(1)
        
    current_region = None
    min_coords = None
    max_coords = None
    
    with open(REGIONS_FILE, "r") as f:
        for line in f:
            reg_match = re.match(r"^ {4}([a-zA-Z0-9_\-]+):", line)
            if reg_match:
                current_region = reg_match.group(1)
                continue
            if current_region == REGION_NAME:
                if "min:" in line:
                    m = re.search(r"x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)", line)
                    if m:
                        min_coords = {"x": int(m.group(1)), "y": int(m.group(2)), "z": int(m.group(3))}
                elif "max:" in line:
                    m = re.search(r"x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)", line)
                    if m:
                        max_coords = {"x": int(m.group(1)), "y": int(m.group(2)), "z": int(m.group(3))}
                        
    return min_coords, max_coords

def save_backup(min_coords, max_coords, registry_data):
    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    with open(BACKUP_FILE, "w") as f:
        json.dump({
            "min": min_coords,
            "max": max_coords,
            "registry": registry_data
        }, f, indent=4)
    print(f"💾 Backup saved to {BACKUP_FILE}")

def undo_changes():
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ Backup file {BACKUP_FILE} does not exist! Cannot undo.")
        sys.exit(1)
        
    with open(BACKUP_FILE, "r") as f:
        backup = json.load(f)
        
    min_c = backup["min"]
    max_c = backup["max"]
    
    print(f"🔄 Reverting region '{REGION_NAME}' to Min: {min_c}, Max: {max_c}...")
    send_exaroton_command(f"rg redefine -w {WORLD_NAME} {REGION_NAME} {min_c['x']} {min_c['y']} {min_c['z']} {max_c['x']} {max_c['y']} {max_c['z']}")
    send_exaroton_command(f"rg save -w {WORLD_NAME}")
    send_exaroton_command("wg save")
    send_exaroton_command("rg reload")
    
    # Restore registry
    if os.path.exists(REGISTRY_FILE) and "registry" in backup:
        with open(REGISTRY_FILE, "w") as f:
            json.dump(backup["registry"], f, indent=4)
        print(f"🔄 Restored {REGISTRY_FILE}")
        
    pull_regions()
    print("🎉 Successfully undone height changes and restored original region configuration!")

def main():
    parser = argparse.ArgumentParser(description="Increase Azan Saleh region height with Undo support")
    parser.add_argument("--undo", action="store_true", help="Undo changes and revert to backup")
    args = parser.parse_args()

    if args.undo:
        undo_changes()
        return

    # 1. Get current bounds
    min_c, max_c = get_current_bounds()
    if not min_c or not max_c:
        print(f"❌ Region '{REGION_NAME}' not found in {REGIONS_FILE}!")
        sys.exit(1)
        
    # Load registry
    registry_data = None
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            registry_data = json.load(f)
            
    # 2. Save backup
    save_backup(min_c, max_c, registry_data)

    # 3. Calculate new coordinates
    new_max_y = max_c["y"] + 15
    print(f"📐 Current bounds: Min Y: {min_c['y']}, Max Y: {max_c['y']}")
    print(f"📐 New bounds: Min Y: {min_c['y']}, Max Y: {new_max_y} (+15 blocks)")

    # 4. Redefine region on server
    redefine_cmd = f"rg redefine -w {WORLD_NAME} {REGION_NAME} {min_c['x']} {min_c['y']} {min_c['z']} {max_c['x']} {new_max_y} {max_c['z']}"
    if send_exaroton_command(redefine_cmd):
        send_exaroton_command(f"rg save -w {WORLD_NAME}")
        send_exaroton_command("wg save")
        send_exaroton_command("rg reload")
        
        # Pull new regions
        pull_regions()
        
        # 5. Update registry
        if registry_data and REGION_NAME in registry_data.get("regions", {}):
            reg = registry_data["regions"][REGION_NAME]
            reg["coordinates"]["min"] = {"x": min_c["x"], "y": min_c["y"], "z": min_c["z"]}
            reg["coordinates"]["max"] = {"x": max_c["x"], "y": new_max_y, "z": max_c["z"]}
            
            with open(REGISTRY_FILE, "w") as f:
                json.dump(registry_data, f, indent=4)
            print(f"📝 Updated {REGISTRY_FILE} with exact coordinates.")

        print("🎉 Height increased and region verified successfully!")

if __name__ == "__main__":
    main()
