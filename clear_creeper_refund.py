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
BACKUP_FILE = "backup_clear_creeper.json"

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

def clear_and_refund():
    # 1. Backup state
    backup_data = {
        "region": "hanansaleh",
        "flag_cleared": "other-explosion",
        "refund_count": 32,
        "refund_item": "emerald"
    }
    with open(BACKUP_FILE, "w") as f:
        json.dump(backup_data, f, indent=2)
    print(f"💾 Backup saved to {BACKUP_FILE}")

    # 2. Clear other-explosion flag from region hanansaleh
    send_command("rg flag -w \"world\" hanansaleh other-explosion")
    send_command("wg save")

    # 3. Give 32 emeralds refund
    send_command("give hanansaleh emerald 32")

    # 4. Notify player privately
    send_command("msg hanansaleh §6[Refund] §eYour Creeper protection upgrade has been cleared and 32 Emeralds refunded!")

    # 5. Remove Creeper trade entries from processed_trades.json
    processed_file = "Shopkeepers/processed_trades.json"
    if os.path.exists(processed_file):
        with open(processed_file, "r") as f:
            trades = json.load(f)
        if isinstance(trades, list):
            filtered = [t for t in trades if not ("hanansaleh" in str(t) and "WRITTEN_BOOK" in str(t))]
            with open(processed_file, "w") as f:
                json.dump(filtered, f, indent=2)
            # Sync to server
            subprocess.run([sys.executable, "sync.py", "push", processed_file], capture_output=True)
            print("Updated and synced processed_trades.json")

    print("\n🎉 Creeper protection cleared, 32 Emeralds refunded, and player notified privately!")

def undo():
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ Backup file {BACKUP_FILE} not found!")
        sys.exit(1)
    
    send_command("rg flag -w \"world\" hanansaleh other-explosion deny")
    send_command("wg save")
    send_command("clear hanansaleh emerald 32")
    send_command("msg hanansaleh §6[Undo] §eYour Creeper protection flag has been restored.")
    print("✅ Rollback completed successfully.")

if __name__ == "__main__":
    if "--undo" in sys.argv:
        undo()
    else:
        clear_and_refund()
