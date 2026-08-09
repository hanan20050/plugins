#!/usr/bin/env python3
"""
Rename region `manansaleh2007_farm` to `manan1` in WorldGuard/worlds/world/regions.yml and player_regions_registry.json.

Preserves all region boundaries, flags, and owner/member UUIDs.
Supports --undo and --dry-run options.
"""

import os
import sys
import json
import subprocess
import argparse

REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"
REGISTRY_FILE = "player_regions_registry.json"
BACKUP_DIR = "WorldGuard/backups"
BACKUP_FILE_REGIONS = os.path.join(BACKUP_DIR, "rename_manan_farm_regions_backup.json")
BACKUP_FILE_REGISTRY = os.path.join(BACKUP_DIR, "rename_manan_farm_registry_backup.json")

def send_exaroton_command(cmd, dry_run=False):
    if dry_run:
        print(f"[DRY-RUN] Console Command: {cmd}")
        return True

    ENV_FILE = ".env"
    config = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()

    token = os.environ.get("EXAROTON_TOKEN") or config.get("EXAROTON_TOKEN") or "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
    server_id = os.environ.get("EXAROTON_SERVER_ID") or config.get("EXAROTON_SERVER_ID") or "cEuS61sZvNEFS3aB"

    url = f"https://api.exaroton.com/v1/servers/{server_id}/command/"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {token}",
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

def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if os.path.exists(REGIONS_FILE):
        with open(REGIONS_FILE, "r") as f:
            content = f.read()
        with open(BACKUP_FILE_REGIONS, "w") as f:
            json.dump({"raw_regions_yml": content}, f, indent=2)
        print(f"Backed up {REGIONS_FILE} to {BACKUP_FILE_REGIONS}")
        
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            content = f.read()
        with open(BACKUP_FILE_REGISTRY, "w") as f:
            json.dump({"raw_registry_json": content}, f, indent=2)
        print(f"Backed up {REGISTRY_FILE} to {BACKUP_FILE_REGISTRY}")

def rename_region(dry_run=False):
    backup()

    # Edit regions.yml
    with open(REGIONS_FILE, "r") as f:
        regions_content = f.read()

    old_key_wg = "  manansaleh2007_farm:"
    new_key_wg = "  manan1:"

    if old_key_wg not in regions_content:
        print(f"[ERROR] Key '{old_key_wg}' not found in {REGIONS_FILE}.")
        return False

    updated_regions = regions_content.replace(old_key_wg, new_key_wg, 1)

    # Edit registry
    with open(REGISTRY_FILE, "r") as f:
        registry_data = json.load(f)

    if "manansaleh2007_farm" not in registry_data.get("regions", {}):
        print(f"[ERROR] Key 'manansaleh2007_farm' not found in {REGISTRY_FILE}.")
        return False

    # Swap keys preserving order if possible
    new_regions_dict = {}
    for k, v in registry_data["regions"].items():
        if k == "manansaleh2007_farm":
            new_regions_dict["manan1"] = v
        else:
            new_regions_dict[k] = v
    registry_data["regions"] = new_regions_dict
    
    import datetime
    registry_data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    if dry_run:
        print(f"[DRY-RUN] Would replace '{old_key_wg}' with '{new_key_wg}' in {REGIONS_FILE}.")
        print(f"[DRY-RUN] Would rename 'manansaleh2007_farm' to 'manan1' in {REGISTRY_FILE}.")
        return True

    with open(REGIONS_FILE, "w") as f:
        f.write(updated_regions)
    print(f"Renamed region `manansaleh2007_farm` to `manan1` in {REGIONS_FILE}.")

    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry_data, f, indent=4)
    print(f"Updated registry `manansaleh2007_farm` to `manan1` in {REGISTRY_FILE}.")

    # Sync to Exaroton
    subprocess.run(["python3", "sync.py", "push", REGIONS_FILE], check=True)
    subprocess.run(["python3", "sync.py", "push", REGISTRY_FILE], check=True)

    # Reload WorldGuard
    send_exaroton_command("rg reload")
    print("Pushed files to Exaroton server and reloaded WorldGuard plugin.")
    return True

def undo(dry_run=False):
    if not os.path.exists(BACKUP_FILE_REGIONS) or not os.path.exists(BACKUP_FILE_REGISTRY):
        print(f"[ERROR] Backup files not found.")
        return False

    with open(BACKUP_FILE_REGIONS, "r") as f:
        regions_data = json.load(f)
    with open(BACKUP_FILE_REGISTRY, "r") as f:
        registry_data = json.load(f)

    if dry_run:
        print(f"[DRY-RUN] Would restore {REGIONS_FILE} and {REGISTRY_FILE} from backups.")
        return True

    with open(REGIONS_FILE, "w") as f:
        f.write(regions_data["raw_regions_yml"])
    print(f"Restored {REGIONS_FILE} from backup.")

    with open(REGISTRY_FILE, "w") as f:
        f.write(registry_data["raw_registry_json"])
    print(f"Restored {REGISTRY_FILE} from backup.")

    subprocess.run(["python3", "sync.py", "push", REGIONS_FILE], check=True)
    subprocess.run(["python3", "sync.py", "push", REGISTRY_FILE], check=True)
    send_exaroton_command("rg reload")
    print("Pushed files to Exaroton and reloaded WorldGuard plugin.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Rename region manansaleh2007_farm to manan1.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying files")
    parser.add_argument("--undo", action="store_true", help="Undo region renaming by restoring previous configurations")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        rename_region(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
