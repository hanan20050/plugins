#!/usr/bin/env python3
"""
Grant Rayan Saleh (NightmareDady) membership to Manan's End Farm (manan_end_farm) in world_the_end
with full Undo/Rollback support and private player notification.
"""

import os
import sys
import json
import re
import subprocess
import argparse

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

WORLD_NAME = "world_the_end"
REGION_NAME = "manan_end_farm"
TARGET_PLAYER_NAME = "NightmareDady"
TARGET_PLAYER_UUID = "d413c28e-64bb-32af-9661-3e901bc6e22b"
REGIONS_FILE = f"WorldGuard/worlds/{WORLD_NAME}/regions.yml"
BACKUP_FILE = f"WorldGuard/backups/{REGION_NAME}_membership_backup.json"

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

def backup_current_state():
    pull_regions()
    if not os.path.exists(REGIONS_FILE):
        print(f"❌ Regions file {REGIONS_FILE} not found!")
        sys.exit(1)
        
    with open(REGIONS_FILE, "r") as f:
        content = f.read()
        
    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    with open(BACKUP_FILE, "w") as f:
        f.write(content)
    print(f"💾 Backup saved to {BACKUP_FILE}")

def undo_changes():
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ Backup file {BACKUP_FILE} does not exist! Cannot undo.")
        sys.exit(1)
        
    with open(BACKUP_FILE, "r") as f:
        backup_content = f.read()
        
    with open(REGIONS_FILE, "w") as f:
        f.write(backup_content)
        
    push_regions()
    send_exaroton_command("wg reload")
    send_exaroton_command(f"msg {TARGET_PLAYER_NAME} Your membership to Manan's End Farm region ({REGION_NAME}) has been revoked.")
    print("🎉 Successfully undone membership changes and restored original region configuration!")

def main():
    parser = argparse.ArgumentParser(description="Grant Rayan Saleh End Farm membership with Undo support")
    parser.add_argument("--undo", action="store_true", help="Undo changes and revert to backup")
    args = parser.parse_args()

    if args.undo:
        undo_changes()
        return

    # 1. Backup state
    backup_current_state()

    # 2. Issue console command to add member
    print(f"👤 Adding {TARGET_PLAYER_NAME} to region '{REGION_NAME}' in world '{WORLD_NAME}'...")
    send_exaroton_command(f"rg addmember -w \"{WORLD_NAME}\" {REGION_NAME} {TARGET_PLAYER_NAME}")
    send_exaroton_command("wg save")

    # 3. Pull updated region file
    pull_regions()

    # 4. Verify region file has UUID included per strict rule
    needs_push = False
    with open(REGIONS_FILE, "r") as f:
        lines = f.readlines()

    # Check if target player UUID is in members.unique-ids
    in_target_region = False
    in_members = False
    has_uuid = False

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith(f"{REGION_NAME}:"):
            in_target_region = True
        elif line.startswith("    ") and not line.startswith("        ") and in_target_region:
            in_target_region = False

        if in_target_region and "members:" in line:
            in_members = True
            new_lines.append(line)
            i += 1
            # Check next lines under members
            while i < len(lines) and lines[i].startswith("            "):
                m_line = lines[i]
                if "unique-ids:" in m_line:
                    if TARGET_PLAYER_UUID in m_line:
                        has_uuid = True
                    else:
                        # Append UUID to unique-ids list
                        if "[]" in m_line or "{}" in m_line:
                            m_line = f"            unique-ids: [{TARGET_PLAYER_UUID}]\n"
                        elif "]" in m_line:
                            m_line = m_line.replace("]", f", {TARGET_PLAYER_UUID}]")
                        has_uuid = True
                        needs_push = True
                new_lines.append(m_line)
                i += 1
            if not has_uuid:
                # If unique-ids was not present under members (e.g. members: {})
                # replace members line or insert unique-ids
                if "members: {}" in new_lines[-1]:
                    new_lines[-1] = "        members:\n            unique-ids: [" + TARGET_PLAYER_UUID + "]\n"
                else:
                    new_lines.append("            unique-ids: [" + TARGET_PLAYER_UUID + "]\n")
                has_uuid = True
                needs_push = True
            continue

        new_lines.append(line)
        i += 1

    if needs_push:
        print("✏️ Enforcing UUID in regions.yml for Geyser/Bedrock compatibility...")
        with open(REGIONS_FILE, "w") as f:
            f.writelines(new_lines)
        push_regions()
        send_exaroton_command("wg reload")

    # 5. Send private in-game message to Rayan Saleh ONLY
    print(f"📩 Sending private notification to {TARGET_PLAYER_NAME}...")
    msg_cmd = f"msg {TARGET_PLAYER_NAME} You have been added as a member to Manan's End Farm region ({REGION_NAME})!"
    send_exaroton_command(msg_cmd)

    print("🎉 Membership granted, region verified, and private notification sent to Rayan Saleh successfully!")

if __name__ == "__main__":
    main()
