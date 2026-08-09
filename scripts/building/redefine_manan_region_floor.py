#!/usr/bin/env python3
"""
Redefine Manan Saleh's region floor to 1 level above (Y=65 instead of Y=64).
Modifies `manansaleh2007` and `hastybag7675_manansaleh2007` regions in WorldGuard/worlds/world/regions.yml.

Supports --undo to restore previous region definitions.
"""

import os
import sys
import json
import subprocess

REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"
BACKUP_DIR = "WorldGuard/backups"
BACKUP_FILE = os.path.join(BACKUP_DIR, "redefine_manan_floor_backup.json")

def send_exaroton_command(cmd):
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
    print(f"Console Command '{cmd}' output: {res.stdout}")

def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if os.path.exists(REGIONS_FILE):
        with open(REGIONS_FILE, "r") as f:
            content = f.read()
        with open(BACKUP_FILE, "w") as f:
            json.dump({"raw_regions_yml": content}, f, indent=2)
        print(f"Backed up {REGIONS_FILE} to {BACKUP_FILE}")

def undo():
    if not os.path.exists(BACKUP_FILE):
        print(f"No backup file found at {BACKUP_FILE}")
        sys.exit(1)
    with open(BACKUP_FILE, "r") as f:
        data = json.load(f)
    with open(REGIONS_FILE, "w") as f:
        f.write(data["raw_regions_yml"])
    print(f"Restored {REGIONS_FILE} from {BACKUP_FILE}")
    
    # Sync and reload WorldGuard
    subprocess.run(["python3", "sync.py", "push", REGIONS_FILE], check=True)
    send_exaroton_command("rg reload")
    print("Undo completed: Restored region floor to Y=64 and reloaded WorldGuard.")

def redefine_floor():
    backup()

    with open(REGIONS_FILE, "r") as f:
        content = f.read()

    # Replace min Y from 64 to 65 for manan regions
    # manansaleh2007 & hastybag7675_manansaleh2007: min: {x: 1256, y: 64, z: -229} -> min: {x: 1256, y: 65, z: -229}
    old_min_line = "min: {x: 1256, y: 64, z: -229}"
    new_min_line = "min: {x: 1256, y: 65, z: -229}"

    if old_min_line not in content:
        print(f"[WARNING] Could not find exact string '{old_min_line}' in {REGIONS_FILE}.")
    
    updated_content = content.replace(old_min_line, new_min_line)

    with open(REGIONS_FILE, "w") as f:
        f.write(updated_content)

    print("Updated WorldGuard region floor boundary for Manan's region (min Y set to 65).")

    # Push to Exaroton
    subprocess.run(["python3", "sync.py", "push", REGIONS_FILE], check=True)

    # Reload WorldGuard
    send_exaroton_command("rg reload")
    print("Pushed regions.yml to Exaroton and reloaded WorldGuard.")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--undo":
        undo()
    else:
        redefine_floor()

if __name__ == "__main__":
    main()
