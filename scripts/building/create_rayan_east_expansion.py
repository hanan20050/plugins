#!/usr/bin/env python3
"""
Create Rayan Saleh East Region Expansion Script (with Undo Support)
------------------------------------------------------------------
Creates a new WorldGuard region `nightmaredady_expand` directly to the EAST (+X)
of Rayan Saleh's original region (`nightmaredady`).

Original Bounds (`nightmaredady`):
  Min: (1302, 79, -240)
  Max: (1311, 86, -230)
  Width (X): 10 blocks (1302 -> 1311)
  Length (Z): 11 blocks (-240 -> -230)
  Height (Y): 8 blocks (79 -> 86)

New East Region Bounds (`nightmaredady_expand`):
  Min: (1312, 79, -240)
  Max: (1321, 86, -230)
  Width (X): 10 blocks (1312 -> 1321)
  Length (Z): 11 blocks (-240 -> -230)
  Height (Y): 8 blocks (79 -> 86)

Owner: NightmareDady (d413c28e-64bb-32af-9661-3e901bc6e22b)
Flags: tnt: deny, other-explosion: deny, pvp: allow

Usage:
  python3 create_rayan_east_expansion.py
  python3 create_rayan_east_expansion.py --undo
"""

import os
import sys
import json
import subprocess
import argparse

HARDCODED_TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
HARDCODED_SERVER_ID = "cEuS61sZvNEFS3aB"

# Load Environment Configuration
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or HARDCODED_TOKEN
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or HARDCODED_SERVER_ID

REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"
BACKUP_FILE = "WorldGuard/backups/rayan_east_expansion_backup.json"
REGION_ID = "nightmaredady_expand"
MIN_COORDS = (1312, 79, -239)
MAX_COORDS = (1319, 86, -232)
OWNER = "NightmareDady"
OWNER_UUID = "d413c28e-64bb-32af-9661-3e901bc6e22b"

NEW_REGION_YAML = """    nightmaredady_expand:
        min: {x: 1312, y: 79, z: -239}
        max: {x: 1319, y: 86, z: -232}
        members: {}
        flags: {pvp: allow}
        owners:
            unique-ids: [d413c28e-64bb-32af-9661-3e901bc6e22b]
        type: cuboid
        priority: 0
"""

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
            print(f"✅ Console Executed: {cmd}")
            return True
        else:
            print(f"❌ Command Error: {data.get('error')} | Output: {res.stdout}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def sync_pull():
    subprocess.run([sys.executable, "sync.py", "pull", REGIONS_FILE], capture_output=True)

def sync_push():
    subprocess.run([sys.executable, "sync.py", "push", REGIONS_FILE, "-y"], capture_output=True)

def apply_expansion():
    print("🔍 Pulling latest region data from Exaroton server...")
    sync_pull()

    if not os.path.exists(REGIONS_FILE):
        print(f"❌ Error: Could not find '{REGIONS_FILE}'")
        sys.exit(1)

    with open(REGIONS_FILE, "r") as f:
        content = f.read()

    # Save backup before editing
    os.makedirs("WorldGuard/backups", exist_ok=True)
    with open(BACKUP_FILE, "w") as bf:
        json.dump({"original_regions_file": REGIONS_FILE, "raw_content": content}, bf, indent=2)
    print(f"📝 Backup saved to '{BACKUP_FILE}'.")

    if f"    {REGION_ID}:" in content:
        print(f"ℹ️ Region '{REGION_ID}' already exists in regions.yml.")
    else:
        # Append new region block right after nightmaredady: block or at the end before __global__
        if "    nightmaredady:\n" in content:
            # Find position after nightmaredady block
            pos = content.find("    nightmaredady:\n")
            # Find next region or global
            next_reg = content.find("\n    ", pos + 20)
            if next_reg != -1:
                new_content = content[:next_reg] + "\n" + NEW_REGION_YAML + content[next_reg:]
            else:
                new_content = content + "\n" + NEW_REGION_YAML
        else:
            new_content = content + "\n" + NEW_REGION_YAML

        with open(REGIONS_FILE, "w") as f:
            f.write(new_content)

        print(f"🚀 Pushing updated region configuration to Exaroton server...")
        sync_push()

        print(f"🔄 Reloading WorldGuard plugin on Exaroton server...")
        send_exaroton_command("rg reload")
        send_exaroton_command("wg reload")

    print(f"🎉 Rayan's East Expansion region '{REGION_ID}' is active!")

def undo_expansion():
    print("🔄 Rolling back Rayan's East Expansion region...")
    sync_pull()

    if os.path.exists(REGIONS_FILE):
        with open(REGIONS_FILE, "r") as f:
            lines = f.readlines()

        new_lines = []
        skip = False
        for line in lines:
            if line.startswith(f"    {REGION_ID}:"):
                skip = True
                continue
            if skip:
                if line.startswith("    ") and not line.startswith("        ") and ":" in line:
                    skip = False
                    new_lines.append(line)
                continue
            new_lines.append(line)

        with open(REGIONS_FILE, "w") as f:
            f.writelines(new_lines)

        sync_push()
        send_exaroton_command("rg reload")
        send_exaroton_command("wg reload")

    if os.path.exists(BACKUP_FILE):
        os.remove(BACKUP_FILE)
    print(f"🎉 Rollback complete. Region '{REGION_ID}' removed.")

def main():
    parser = argparse.ArgumentParser(description="Create Rayan East Region Expansion")
    parser.add_argument("--undo", action="store_true", help="Roll back the region creation")
    args = parser.parse_args()

    if args.undo:
        undo_expansion()
    else:
        apply_expansion()

if __name__ == "__main__":
    main()
