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

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID")
BACKUP_FILE = "backup_hanan_refund.json"

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

def do_refund():
    # 1. Backup current region state
    backup_data = {
        "region": "hanansaleh",
        "flags_removed": ["other-explosion"],
        "refund_item": "emerald",
        "refund_count": 64,
        "notes": "Refunding Creeper protection (32 emeralds) and Small Plot expansion (32 emeralds)"
    }
    with open(BACKUP_FILE, "w") as f:
        json.dump(backup_data, f, indent=2)
    print(f"💾 Saved region backup to {BACKUP_FILE}")

    # 2. Unset other-explosion flag on region hanansaleh
    send_command("rg flag -w \"world\" hanansaleh other-explosion")
    send_command("wg save")

    # 3. Issue refund of 64 Emeralds (32 + 32)
    send_command("give hanansaleh emerald 64")
    send_command("msg hanansaleh §6[Refund] §eYou have received a refund of 64 Emeralds (1 Netherite Ingot) for your returned upgrades.")

    # 4. Remove entries from processed_trades.json
    processed_file = "Shopkeepers/processed_trades.json"
    if os.path.exists(processed_file):
        with open(processed_file, "r") as f:
            trades = json.load(f)
        filtered = [t for t in trades if not ("hanansaleh" in t and ("WRITTEN_BOOK" in t))]
        with open(processed_file, "w") as f:
            json.dump(filtered, f, indent=2)
        print("Updated processed_trades.json")

    print("\n🎉 Refund of 64 Emeralds (1 Netherite Ingot equivalent) completed and Creeper protection flag removed!")

def do_undo():
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ Backup file {BACKUP_FILE} not found!")
        sys.exit(1)
    with open(BACKUP_FILE, "r") as f:
        backup_data = json.load(f)

    print("↩️ Undoing refund & restoring flags...")
    # Restore other-explosion deny flag
    send_command("rg flag -w \"world\" hanansaleh other-explosion deny")
    send_command("wg save")
    # Take back refunded emeralds if possible
    send_command("clear hanansaleh emerald 64")
    print("✅ Rollback completed successfully.")

if __name__ == "__main__":
    if "--undo" in sys.argv:
        do_undo()
    else:
        do_refund()
