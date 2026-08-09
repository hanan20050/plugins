#!/usr/bin/env python3
"""
Transfer ownership of the `mon_jin_deku` region to Azan Saleh (azansalehhh).
Updates WorldGuard regions.yml and player_regions_registry.json.
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
AZAN_UUID = "2d5bf9b3-5a85-3026-a136-4680097f11f1"
MONJIN_UUID = "00000000-0000-0000-0009-01fa2d270090"

REGISTRY_FILE = "player_regions_registry.json"
REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"
BACKUP_FILE = f"WorldGuard/backups/{REGION_ID}_assign_azan_backup.json"

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
    parser = argparse.ArgumentParser(description="Assign Monjin region to Azan Saleh")
    parser.add_argument("--undo", action="store_true", help="Undo assignment and revert to Monjin ownership")
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

        print("🔄 Reverting WorldGuard region yml to Monjin ownership...")
        with open(REGIONS_FILE, "r") as f:
            regions_content = f.read()

        old_owner_line = f"unique-ids: [{AZAN_UUID}]"
        new_owner_line = f"unique-ids: [{MONJIN_UUID}]"
        regions_content = regions_content.replace(old_owner_line, new_owner_line)

        with open(REGIONS_FILE, "w") as f:
            f.write(regions_content)

        push_file(REGIONS_FILE)
        send_exaroton_command("rg reload")

        # Restore registry
        registry_data["regions"][REGION_ID] = backup_data["registry_entry"]
        with open(REGISTRY_FILE, "w") as f:
            json.dump(registry_data, f, indent=4)
        push_file(REGISTRY_FILE)
        print("🎉 Successfully reverted Monjin's region ownership back to Monjin!")
        return

    # Original region entry backup
    if REGION_ID not in registry_data["regions"]:
        print(f"❌ Region {REGION_ID} not found in registry!")
        sys.exit(1)

    original_entry = registry_data["regions"][REGION_ID]

    # Save backup details
    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    backup_data = {
        "registry_entry": original_entry
    }
    with open(BACKUP_FILE, "w") as f:
        json.dump(backup_data, f, indent=4)
    print(f"💾 Backup saved to {BACKUP_FILE}")

    # Transfer ownership in regions.yml
    print(f"👤 Assigning region '{REGION_ID}' to Azan Saleh ({AZAN_UUID}) in regions.yml...")
    with open(REGIONS_FILE, "r") as f:
        regions_content = f.read()

    # Find the mon_jin_deku section block and replace unique-ids under owners
    old_owner_block = f"        owners:\n            unique-ids: [{MONJIN_UUID}]"
    new_owner_block = f"        owners:\n            unique-ids: [{AZAN_UUID}]"

    if old_owner_block not in regions_content:
        # Fallback to standard check if formatting differs
        old_owner_block_alt = f"            unique-ids: [{MONJIN_UUID}]"
        new_owner_block_alt = f"            unique-ids: [{AZAN_UUID}]"
        if old_owner_block_alt in regions_content:
            regions_content = regions_content.replace(old_owner_block_alt, new_owner_block_alt)
        else:
            print("❌ Error: Could not locate Monjin's unique-ids under owners in regions.yml!")
            sys.exit(1)
    else:
        regions_content = regions_content.replace(old_owner_block, new_owner_block)

    with open(REGIONS_FILE, "w") as f:
        f.write(regions_content)

    push_file(REGIONS_FILE)
    send_exaroton_command("rg reload")

    # Update player registry entry
    registry_data["regions"][REGION_ID] = {
        "player_name": "azan saleh",
        "username": "azansalehhh",
        "min_corner": original_entry["min_corner"],
        "max_corner": original_entry["max_corner"],
        "dimensions": original_entry["dimensions"],
        "surface_area_sq_blocks": original_entry["surface_area_sq_blocks"],
        "size_category": original_entry["size_category"],
        "floor_y_level": original_entry.get("floor_y_level", 62),
        "raw_uuids": AZAN_UUID
    }

    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry_data, f, indent=4)
    push_file(REGISTRY_FILE)
    print("🎉 Successfully transferred region ownership and updated registry!")

if __name__ == "__main__":
    main()
