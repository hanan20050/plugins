#!/usr/bin/env python3
"""
Rename region `mustafa_azan_rayan` to `combined_region` in WorldGuard/worlds/world/regions.yml.

Preserves all region boundaries, flags, and owner/member UUIDs.
Supports --undo and --dry-run options.
"""

import os
import sys
import json
import subprocess
import argparse

REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"
BACKUP_DIR = "WorldGuard/backups"
BACKUP_FILE = os.path.join(BACKUP_DIR, "rename_combined_region_backup.json")

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
        with open(BACKUP_FILE, "w") as f:
            json.dump({"raw_regions_yml": content}, f, indent=2)
        print(f"Backed up {REGIONS_FILE} to {BACKUP_FILE}")

def rename_region(dry_run=False):
    backup()

    with open(REGIONS_FILE, "r") as f:
        content = f.read()

    old_key = "    mustafa_azan_rayan:"
    new_key = "    combined_region:"

    if old_key not in content:
        print(f"[ERROR] Key '{old_key}' not found in {REGIONS_FILE}.")
        return False

    updated_content = content.replace(old_key, new_key, 1)

    if dry_run:
        print(f"[DRY-RUN] Would replace '{old_key}' with '{new_key}' in {REGIONS_FILE}.")
        return True

    with open(REGIONS_FILE, "w") as f:
        f.write(updated_content)

    print(f"Renamed region `mustafa_azan_rayan` to `combined_region` in {REGIONS_FILE}.")

    # Sync to Exaroton
    subprocess.run(["python3", "sync.py", "push", REGIONS_FILE], check=True)

    # Reload WorldGuard
    send_exaroton_command("rg reload")
    print("Pushed regions.yml to Exaroton server and reloaded WorldGuard plugin.")
    return True

def undo(dry_run=False):
    if not os.path.exists(BACKUP_FILE):
        print(f"[ERROR] Backup file not found: {BACKUP_FILE}")
        return False

    with open(BACKUP_FILE, "r") as f:
        data = json.load(f)

    if dry_run:
        print(f"[DRY-RUN] Would restore {REGIONS_FILE} from {BACKUP_FILE}.")
        return True

    with open(REGIONS_FILE, "w") as f:
        f.write(data["raw_regions_yml"])

    print(f"Restored {REGIONS_FILE} from {BACKUP_FILE}.")

    subprocess.run(["python3", "sync.py", "push", REGIONS_FILE], check=True)
    send_exaroton_command("rg reload")
    print("Pushed regions.yml to Exaroton and reloaded WorldGuard plugin.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Rename region mustafa_azan_rayan to combined_region.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying files")
    parser.add_argument("--undo", action="store_true", help="Undo region renaming by restoring previous regions.yml")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        rename_region(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
