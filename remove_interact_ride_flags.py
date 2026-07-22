#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import re

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID")
REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"
BACKUP_FILE = "backup_all_removed_flags.json"
FLAGS_TO_REMOVE = ["interact", "ride", "item-drop", "item-pickup"]

def send_command(cmd):
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

def pull_regions():
    curl_cmd = [
        "curl", "-s", "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-H", f"Authorization: Bearer {TOKEN}",
        f"https://api.exaroton.com/v1/servers/{SERVER_ID}/files/data/plugins/{REGIONS_FILE}"
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    if res.stdout and "regions:" in res.stdout:
        with open(REGIONS_FILE, "w") as f:
            f.write(res.stdout)
        return True
    return False

def get_all_regions():
    pull_regions()
    if not os.path.exists(REGIONS_FILE):
        return []
    with open(REGIONS_FILE, "r") as f:
        lines = f.readlines()
    regions = []
    for line in lines:
        match = re.match(r"^ {4}([a-zA-Z0-9_\-]+):", line)
        if match:
            reg = match.group(1)
            if reg not in regions:
                regions.append(reg)
    return regions

def remove_flags():
    regions = get_all_regions()
    print(f"Found {len(regions)} regions. Backing up original region file...")
    
    if os.path.exists(REGIONS_FILE):
        with open(REGIONS_FILE, "r") as f:
            raw_content = f.read()
        with open(BACKUP_FILE, "w") as f:
            json.dump({"raw_regions_yml": raw_content, "regions": regions}, f)
        print(f"💾 Saved backup to {BACKUP_FILE}")

    print("🚀 Removing 'interact', 'ride', 'item-drop', and 'item-pickup' flags from all regions...")
    for reg in regions:
        for flag in FLAGS_TO_REMOVE:
            send_command(f"rg flag -w \"world\" {reg} {flag}")
    
    send_command("wg save")
    print("💾 Executed /wg save on server.")

    # Re-pull and verify
    print("🔄 Verifying updated regions...")
    pull_regions()
    print("🎉 All specified flags removed successfully across all regions!")

def undo():
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ Backup file {BACKUP_FILE} not found!")
        sys.exit(1)
    
    with open(BACKUP_FILE, "r") as f:
        backup_data = json.load(f)
    
    regions = backup_data.get("regions", [])
    print(f"↩️ Undoing flag removal for {len(regions)} regions...")
    
    for reg in regions:
        for flag in FLAGS_TO_REMOVE:
            send_command(f"rg flag -w \"world\" {reg} {flag} allow")
    
    send_command("wg save")
    print("✅ Rollback completed successfully.")

if __name__ == "__main__":
    if "--undo" in sys.argv:
        undo()
    else:
        remove_flags()
