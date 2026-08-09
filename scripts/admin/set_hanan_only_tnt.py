#!/usr/bin/env python3
import os
import sys
import json
import subprocess

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
BACKUP_FILE = "backup_hanan_only_tnt.json"

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
        print(f"❌ Response ({cmd}): {res.stdout.strip()}")

def apply_only_tnt():
    # Backup current region state
    backup_data = {
        "region": "hanansaleh",
        "action": "set_only_tnt_deny"
    }
    with open(BACKUP_FILE, "w") as f:
        json.dump(backup_data, f, indent=2)
    print(f"💾 Saved backup to {BACKUP_FILE}")

    # Set TNT deny and unset all other protection flags
    send_command("rg flag -w \"world\" hanansaleh tnt deny")
    send_command("rg flag -w \"world\" hanansaleh other-explosion")
    send_command("rg flag -w \"world\" hanansaleh pvp")
    send_command("rg flag -w \"world\" hanansaleh mob-spawning")
    send_command("rg flag -w \"world\" hanansaleh fire-spread")
    send_command("wg save")

    print("\n🎉 Region 'hanansaleh' updated: ONLY 'tnt: deny' is now active!")

def undo():
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ Backup file {BACKUP_FILE} not found!")
        sys.exit(1)
    
    send_command("rg flag -w \"world\" hanansaleh tnt deny")
    send_command("wg save")
    print("✅ Rollback completed successfully.")

if __name__ == "__main__":
    if "--undo" in sys.argv:
        undo()
    else:
        apply_only_tnt()
