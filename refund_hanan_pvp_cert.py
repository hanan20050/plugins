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
BACKUP_FILE = "backup_hanan_pvp_refund.json"

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
    return res.stdout

def execute_pvp_refund():
    player_name = "hanansaleh"
    refund_amount = 32
    
    print(f"🔍 Attempting to retrieve PvP Protection Certificate book from {player_name} inventory...")
    clear_out = send_command(f"clear {player_name} minecraft:written_book 1")
    print(f"Console response: {clear_out.strip()}")

    # Backup region state
    backup_data = {
        "player": player_name,
        "refund_amount": refund_amount,
        "flag_removed": "pvp"
    }
    with open(BACKUP_FILE, "w") as f:
        json.dump(backup_data, f, indent=2)

    # 1. Unset pvp flag & wg save
    send_command(f"rg flag -w \"world\" {player_name} pvp")
    send_command("wg save")

    # 2. Give 32 emeralds refund
    send_command(f"give {player_name} emerald {refund_amount}")

    # 3. Send private msg notification
    send_command(f"msg {player_name} §6[Refund Complete] §aCertificate returned! §eYour PvP protection upgrade was returned and 32 Emeralds refunded to your inventory.")

    print(f"\n🎉 Successfully processed 32 Emerald PvP refund for {player_name}!")

def undo():
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ Backup file {BACKUP_FILE} not found!")
        sys.exit(1)
    
    send_command("rg flag -w \"world\" hanansaleh pvp -g non_owners deny")
    send_command("wg save")
    send_command("clear hanansaleh emerald 32")
    send_command("msg hanansaleh §6[Undo] §eRollback completed. 32 Emeralds cleared and PvP flag restored.")
    print("✅ Rollback completed successfully.")

if __name__ == "__main__":
    if "--undo" in sys.argv:
        undo()
    else:
        execute_pvp_refund()
