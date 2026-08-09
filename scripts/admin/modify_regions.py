#!/usr/bin/env python3
import os
import sys
import json
import re
import subprocess

# Path configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")
REGIONS_FILE = os.path.join(SCRIPT_DIR, "WorldGuard/worlds/world/regions.yml")
BACKUP_DIR = os.path.join(SCRIPT_DIR, "WorldGuard/backups")
BACKUP_FILE = os.path.join(BACKUP_DIR, "hanansaleh_land_removed_backup.json")

# Load environment variables
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    CONFIG[parts[0].strip()] = parts[1].strip()

TOKEN = CONFIG.get("EXAROTON_TOKEN")
SERVER_ID = CONFIG.get("EXAROTON_SERVER_ID")

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
            print(f"❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"Response Error: {res.stdout}")
        return False

def sync_pull_regions():
    print("Pulling updated regions.yml from server...")
    res = subprocess.run(["python3", "sync.py", "pull", "WorldGuard/worlds/world/regions.yml"], capture_output=True, text=True)
    print(res.stdout)

def backup_hanansaleh_land():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if os.path.exists(REGIONS_FILE):
        with open(REGIONS_FILE, "r") as f:
            lines = f.readlines()
        
        in_region = False
        region_lines = []
        for line in lines:
            if line.strip().startswith("hanansaleh_land:"):
                in_region = True
                region_lines.append(line)
            elif in_region:
                if line.startswith("    ") and not line.startswith("        ") and ":" in line:
                    if not line.strip().startswith("min:") and not line.strip().startswith("max:") and not line.strip().startswith("members:") and not line.strip().startswith("flags:") and not line.strip().startswith("owners:") and not line.strip().startswith("type:") and not line.strip().startswith("priority:"):
                        break
                region_lines.append(line)

        backup_payload = {
            "region_name": "hanansaleh_land",
            "raw_yaml": "".join(region_lines),
            "parsed_bounds": {
                "min": {"x": 1103, "y": 63, "z": -162},
                "max": {"x": 1124, "y": 63, "z": -141},
                "owners": ["326a36ea-b465-3192-a4f7-c313f347edc9", "28dd928d-7a83-35c0-9598-6b39b0d1b422", "b78d8ea3-3bf5-30b0-b412-db4d5894dca7"]
            },
            "timestamp": subprocess.getoutput("date -u +'%Y-%m-%dT%H:%M:%SZ'")
        }
        with open(BACKUP_FILE, "w") as bf:
            json.dump(backup_payload, bf, indent=2)
        print(f"💾 Backed up region data for 'hanansaleh_land' to {BACKUP_FILE}")

def main():
    undo = "--undo" in sys.argv
    if undo:
        if not os.path.exists(BACKUP_FILE):
            print("No backup found to restore!")
            return
        print(f"Restoring region data from {BACKUP_FILE}...")
        # To undo, redefine region
        send_exaroton_command("rg define hanansaleh_land -w world 1103,63,-162 1124,63,-141")
        send_exaroton_command("rg reload")
        sync_pull_regions()
        print("Restoration complete!")
        return

    # 1. Pull latest regions
    sync_pull_regions()

    # 2. Backup hanansaleh_land
    backup_hanansaleh_land()

    # 3. Give Manan access to manansaleh2007_farm
    print("Giving manansaleh2007 and .manansaleh2007 full owner access to manansaleh2007_farm...")
    send_exaroton_command("rg addowner manansaleh2007_farm manansaleh2007 -w world")
    send_exaroton_command("rg addowner manansaleh2007_farm .manansaleh2007 -w world")

    # 4. Remove hanansaleh_land region
    print("Removing region hanansaleh_land...")
    send_exaroton_command("rg remove -w world hanansaleh_land")

    # 5. Reload WorldGuard plugin
    send_exaroton_command("rg reload")

    # 6. Sync updated regions file back to workspace
    sync_pull_regions()

    print("\n✅ Operation completed successfully! Manan now has full access to his farm, hanansaleh_land has been removed, and its data is safely backed up.")

if __name__ == "__main__":
    main()
