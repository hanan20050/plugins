#!/usr/bin/env python3
"""
Creeper Upgrade Refund Script with Mandatory Certificate Removal
------------------------------------------------------------------
Checks and removes 1 Upgrade Certificate (written_book) from player's inventory.
If the certificate book cannot be found or removed, the refund is IMMEDIATELY STOPPED.

Usage:
  python3 clear_creeper_refund.py [player_name] [--undo] [--dry-run]
"""

import os
import sys
import json
import time
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

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID")
BACKUP_FILE = "backup_clear_creeper.json"

def send_command(cmd, dry_run=False):
    if dry_run:
        print(f"[DRY-RUN] Console command: {cmd}")
        return True
    
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
            print(f"❌ Exaroton Command Error: {data.get('error')}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def check_server_logs_for_clear(player_name):
    """Fetches server logs via Exaroton API to confirm item clear success."""
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/logs/"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "GET", url,
        "-H", f"Authorization: Bearer {TOKEN}"
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        content = data.get("data", {}).get("content", "")
        lines = content.splitlines()[-20:] # Inspect last 20 log lines
        for line in reversed(lines):
            line_lower = line.lower()
            if player_name.lower() in line_lower:
                if "removed" in line_lower and "item(s)" in line_lower:
                    if not "removed 0 item(s)" in line_lower:
                        return True, line
                if "cleared" in line_lower and ("item" in line_lower or "items" in line_lower):
                    if not "cleared 0" in line_lower:
                        return True, line
                if "no items were found" in line_lower or "could not clear" in line_lower or "removed 0 item(s)" in line_lower:
                    return False, line
    except Exception as e:
        print(f"⚠️ Log parsing error: {e}")
    return False, "No definitive log line found"

def verify_and_take_book(player_name, dry_run=False):
    """Takes 1 written_book from player inventory. Stops refund if missing."""
    print(f"🔍 Attempting to retrieve upgrade certificate book from {player_name}'s inventory...")
    if dry_run:
        print(f"[DRY-RUN] Would execute: clear {player_name} minecraft:written_book 1")
        return True

    send_command(f"clear {player_name} minecraft:written_book 1")
    time.sleep(1.5) # Allow console execution & log flush

    book_taken, log_evidence = check_server_logs_for_clear(player_name)
    if book_taken:
        print(f"✅ Certificate book successfully taken from {player_name}! Log: {log_evidence}")
        return True
    else:
        print(f"❌ REFUND STOPPED: Could not take upgrade certificate book from {player_name}.")
        print(f"   Reason/Log: {log_evidence}")
        send_command(f"msg {player_name} §6[Refund Stopped] §cCertificate missing! §ePlease place your upgrade certificate book in your inventory to process refund.")
        return False

def clear_and_refund(player_name="hanansaleh", dry_run=False):
    # MANDATORY: Take certificate book back first, otherwise STOP refund
    if not verify_and_take_book(player_name, dry_run):
        print("⛔ Refund aborted because upgrade certificate book was not retrieved.")
        sys.exit(1)

    # 1. Backup state
    backup_data = {
        "region": player_name,
        "flag_cleared": "other-explosion",
        "refund_count": 32,
        "refund_item": "emerald",
        "certificate_taken": True
    }
    if not dry_run:
        with open(BACKUP_FILE, "w") as f:
            json.dump(backup_data, f, indent=2)
        print(f"💾 Backup saved to {BACKUP_FILE}")

    # 2. Clear other-explosion flag from region
    send_command(f"rg flag -w \"world\" {player_name} other-explosion", dry_run)
    send_command("wg save", dry_run)

    # 3. Give 32 emeralds refund
    send_command(f"give {player_name} emerald 32", dry_run)

    # 4. Notify player privately
    send_command(f"msg {player_name} §6[Refund Complete] §eYour certificate was returned. 32 Emeralds refunded!", dry_run)

    # 5. Remove Creeper trade entries from processed_trades.json
    processed_file = "Shopkeepers/processed_trades.json"
    if os.path.exists(processed_file) and not dry_run:
        with open(processed_file, "r") as f:
            trades = json.load(f)
        if isinstance(trades, list):
            filtered = [t for t in trades if not (player_name in str(t) and "WRITTEN_BOOK" in str(t))]
            with open(processed_file, "w") as f:
                json.dump(filtered, f, indent=2)
            # Sync to server
            subprocess.run([sys.executable, "sync.py", "push", processed_file], capture_output=True)
            print("Updated and synced processed_trades.json")

    print("\n🎉 Certificate retrieved, Creeper protection cleared, 32 Emeralds refunded!")

def undo(player_name="hanansaleh", dry_run=False):
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ Backup file {BACKUP_FILE} not found!")
        sys.exit(1)
    
    send_command(f"rg flag -w \"world\" {player_name} other-explosion deny", dry_run)
    send_command("wg save", dry_run)
    send_command(f"clear {player_name} emerald 32", dry_run)
    send_command(f"msg {player_name} §6[Undo] §eYour Creeper protection flag has been restored.", dry_run)
    print("✅ Rollback completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Refund Creeper upgrade with mandatory certificate book check")
    parser.add_argument("player", nargs="?", default="hanansaleh", help="Minecraft player name")
    parser.add_argument("--undo", action="store_true", help="Rollback refund operation")
    parser.add_argument("--dry-run", action="store_true", help="Preview commands")

    args = parser.parse_args()
    if args.undo:
        undo(args.player, args.dry_run)
    else:
        clear_and_refund(args.player, args.dry_run)

if __name__ == "__main__":
    main()
