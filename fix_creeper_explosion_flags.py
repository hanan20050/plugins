#!/usr/bin/env python3
import os
import sys
import json
import subprocess

# Load environment variables
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, val = line.split("=", 1)
                CONFIG[key.strip()] = val.strip()

HARDCODED_TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
HARDCODED_SERVER_ID = "cEuS61sZvNEFS3aB"

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or HARDCODED_TOKEN
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or HARDCODED_SERVER_ID

BACKUP_FILE = os.path.join(os.path.dirname(__file__), "WorldGuard", "backups", "creeper_explosion_fix_backup.json")

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
    if "success" in res.stdout:
        print(f"✅ Executed: {cmd}")
    else:
        print(f"❌ Failed: {cmd} | Response: {res.stdout}")

def main():
    regions_file = os.path.join(os.path.dirname(__file__), "WorldGuard", "worlds", "world", "regions.yml")
    
    # 1. Pull latest regions.yml
    pull_cmd = [sys.executable, "sync.py", "pull", "WorldGuard/worlds/world/regions.yml"]
    subprocess.run(pull_cmd, capture_output=True)

    if "--undo" in sys.argv:
        if not os.path.exists(BACKUP_FILE):
            print("❌ Backup file not found for undo.")
            sys.exit(1)
        with open(BACKUP_FILE, "r") as f:
            backup_data = json.load(f)
        added_regions = backup_data.get("added_creeper_explosion_deny", [])
        print(f"🔄 Rolling back creeper-explosion flag for regions: {added_regions}")
        for reg in added_regions:
            send_exaroton_command(f'rg flag -w "world" {reg} creeper-explosion')
        send_exaroton_command("wg save")
        print("✅ Undo completed successfully!")
        return

    # Back up raw regions.yml
    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    with open(regions_file, "r") as f:
        raw_content = f.read()

    # Identify regions that have other-explosion: deny or are player house regions
    target_regions = [
        "manansaleh2007",
        "hastybag7675_manansaleh2007",
        "azansalehhh",
        "mustafahacker67",
        "combined_region",
        "nightmaredady",
        "manansaleh2007_farm",
        "mustafahacker67_expand",
        "shop"
    ]

    backup_data = {
        "added_creeper_explosion_deny": target_regions,
        "raw_regions_yml": raw_content
    }
    with open(BACKUP_FILE, "w") as f:
        json.dump(backup_data, f, indent=2)

    print(f"📦 Backed up current region config to {BACKUP_FILE}")

    # Apply creeper-explosion deny flag to each target region
    for reg in target_regions:
        print(f"🛡️ Setting creeper-explosion: deny for region '{reg}'...")
        send_exaroton_command(f'rg flag -w "world" {reg} creeper-explosion deny')

    # Save WorldGuard changes
    send_exaroton_command("wg save")
    print("✅ Successfully applied creeper-explosion deny flags to all protected house regions!")

    # Pull updated regions.yml to sync locally
    subprocess.run(pull_cmd, capture_output=True)

if __name__ == "__main__":
    main()
