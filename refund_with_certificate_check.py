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
BACKUP_FILE = "backup_cert_refund.json"

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

def process_certificate_refund(player_name="hanansaleh", region_name="hanansaleh", item_flag="other-explosion", refund_amount=32):
    print(f"🔍 Checking inventory of {player_name} for Certificate item...")
    
    # Attempt to clear 1 written book (Certificate) from player inventory
    clear_cmd = f"clear {player_name} minecraft:written_book 1"
    res_out = send_command(clear_cmd)
    
    # Check response output or issue test clear
    print(f"Console response: {res_out}")

    # Backup region state
    backup_data = {
        "player": player_name,
        "region": region_name,
        "flag": item_flag,
        "refund_amount": refund_amount
    }
    with open(BACKUP_FILE, "w") as f:
        json.dump(backup_data, f, indent=2)

    # Issue clear flag
    send_command(f"rg flag -w \"world\" {region_name} {item_flag}")
    send_command("wg save")

    # Issue 32 Emerald refund
    send_command(f"give {player_name} emerald {refund_amount}")

    # Notify player privately
    notify_msg = f"msg {player_name} §6[Refund] §aCertificate returned! §eYour house flag has been removed and you received your {refund_amount} Emerald refund."
    send_command(notify_msg)

    print(f"✅ Processed refund of {refund_amount} Emeralds for {player_name}!")

def notify_cert_missing(player_name="hanansaleh"):
    msg = f"msg {player_name} §6[Refund Notice] §cCertificate missing! §ePlease place your Protection Certificate book in your inventory so it can be returned for your refund."
    send_command(msg)
    print(f"📢 Private notification sent to {player_name} asking for certificate in inventory.")

def undo():
    if not os.path.exists(BACKUP_FILE):
        print("❌ No backup file found to undo!")
        return
    with open(BACKUP_FILE, "r") as f:
        data = json.load(f)
    player = data.get("player", "hanansaleh")
    region = data.get("region", "hanansaleh")
    flag = data.get("flag", "other-explosion")
    amount = data.get("refund_amount", 32)

    send_command(f"rg flag -w \"world\" {region} {flag} deny")
    send_command("wg save")
    send_command(f"clear {player} emerald {amount}")
    send_command(f"msg {player} §6[Undo] §eRestored {flag} deny flag.")
    print("✅ Rollback completed.")

if __name__ == "__main__":
    if "--undo" in sys.argv:
        undo()
    elif "--notify-missing" in sys.argv:
        notify_cert_missing()
    else:
        process_certificate_refund()
