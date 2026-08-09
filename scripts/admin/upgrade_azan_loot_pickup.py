#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import re

# Load environment variables
ENV_FILE = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if not os.path.exists(ENV_FILE):
    ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")

CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    CONFIG[parts[0].strip()] = parts[1].strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or "cEuS61sZvNEFS3aB"

BACKUP_FILE = os.path.join(os.path.dirname(__file__), "WorldGuard", "backups", "azan_loot_pickup_backup.json")
if not os.path.isabs(BACKUP_FILE):
    BACKUP_FILE = "/Users/hanansaleh/Downloads/plugins/WorldGuard/backups/azan_loot_pickup_backup.json"

TARGET_REGIONS = ["azansalehhh", "mon_jin_deku"]

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
            print(f"✅ Console command executed: {cmd}")
            return True
        else:
            print(f"❌ Error executing command '{cmd}': {data.get('error')}")
            return False
    except Exception as e:
        print(f"Response Error: {res.stdout}")
        return False

def sync_pull_regions():
    print("Pulling updated regions.yml from server...")
    res = subprocess.run([sys.executable, "sync.py", "pull", "WorldGuard/worlds/world/regions.yml", "--force"], capture_output=True, text=True)
    print(res.stdout)

def parse_flags_from_yaml(regions_file, region_id):
    if not os.path.exists(regions_file):
        return {}
    with open(regions_file, "r") as f:
        content = f.read()

    pattern = rf"^\s+{region_id}:\s*\n(.*?)(?=^\s+\w+:|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        return {}
    
    block = match.group(1)
    flags_match = re.search(r"flags:\s*\{(.*?)\}", block, re.DOTALL)
    if not flags_match:
        return {}
    
    flags_str = flags_match.group(1).replace("\n", "").replace("\r", "")
    flags = {}
    parts = flags_str.split(",")
    for part in parts:
        part = part.strip()
        if ":" in part:
            k, v = part.split(":", 1)
            flags[k.strip()] = v.strip()
    return flags

def main():
    sync_pull_regions()

    regions_file = "/Users/hanansaleh/Downloads/plugins/WorldGuard/worlds/world/regions.yml"
    
    if not os.path.exists(regions_file):
        print(f"❌ Regions file not found at {regions_file}")
        sys.exit(1)

    # 1. Backup existing flags
    backup_data = {}
    for region in TARGET_REGIONS:
        backup_data[region] = parse_flags_from_yaml(regions_file, region)
    
    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    
    if "--undo" in sys.argv:
        if not os.path.exists(BACKUP_FILE):
            print("❌ Backup file not found for undo.")
            sys.exit(1)
        with open(BACKUP_FILE, "r") as f:
            saved_backup = json.load(f)
        
        print("🔄 Undoing item-pickup upgrade for Azan's regions...")
        for region in TARGET_REGIONS:
            # Clear item-pickup flags
            send_exaroton_command(f'rg flag -w "world" {region} item-pickup')
            # Restore other flags if backup is present
            old_flags = saved_backup.get(region, {})
            if "item-pickup" in old_flags:
                # restore old value
                val = old_flags["item-pickup"]
                if "item-pickup-group" in old_flags:
                    grp = old_flags["item-pickup-group"]
                    send_exaroton_command(f'rg flag -w "world" {region} -g {grp} item-pickup {val}')
                else:
                    send_exaroton_command(f'rg flag -w "world" {region} item-pickup {val}')
        
        send_exaroton_command("save-all")
        sync_pull_regions()
        print("✅ Undo completed successfully!")
        return

    # Normal Flow: Apply upgrade
    with open(BACKUP_FILE, "w") as f:
        json.dump(backup_data, f, indent=2)
    print(f"💾 Backed up flags to {BACKUP_FILE}")

    for region in TARGET_REGIONS:
        print(f"🛡️ Setting item-pickup flags for '{region}'...")
        # Restrict pickup to owners (meaning deny it for non_owners)
        send_exaroton_command(f'rg flag -w "world" {region} -g NON_OWNERS item-pickup deny')

    send_exaroton_command("save-all")


    sync_pull_regions()
    print("✅ Successfully upgraded Azan Saleh's regions to restrict loot pickup to owners only!")

if __name__ == "__main__":
    main()
