#!/usr/bin/env python3
"""
Temporary 5-Minute Obsidian Selling Special Offer Script
- Temporarily changes Obsidian SELL trade in Sell Drops Shop (Shop ID 2, recipe 35) from 8 Obsidian for 1 Emerald -> to 1 Obsidian for 24 Emeralds (giving players 24 emeralds for selling 1 obsidian!).
- Temporarily REMOVES / DISABLES the Obsidian BUY trade in General Store (Shop ID 1, recipe 38) so players cannot buy obsidian during the offer.
- Synchronizes save.yml to server and reloads Shopkeepers plugin.
- Broadcasts tellraw updates every 10 seconds.
- Automatically reverts trades back to normal after 5 minutes (300 seconds) and reloads Shopkeepers plugin.
"""

import os
import sys
import json
import time
import subprocess

HARDCODED_TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
HARDCODED_SERVER_ID = "cEuS61sZvNEFS3aB"

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

SAVE_YML_PATH = os.path.join(os.path.dirname(__file__), "Shopkeepers", "data", "save.yml")

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

def broadcast_offer_status(elapsed, remaining):
    mins_rem, secs_rem = divmod(remaining, 60)
    time_str = f"{mins_rem}m {secs_rem}s" if mins_rem > 0 else f"{secs_rem}s"
    mins_el, secs_el = divmod(elapsed, 60)
    elapsed_str = f"{mins_el}m {secs_el}s" if mins_el > 0 else f"{secs_el}s"

    msg_json = [
        {"text": "[SPECIAL OFFER] ", "color": "gold", "bold": True},
        {"text": "Sell ", "color": "yellow"},
        {"text": "1 Obsidian", "color": "dark_purple", "bold": True},
        {"text": " ➔ ", "color": "gray"},
        {"text": "24 Emeralds", "color": "green", "bold": True},
        {"text": " | Time: ", "color": "aqua"},
        {"text": time_str, "color": "red", "bold": True},
        {"text": " remaining (Passed: ", "color": "gray"},
        {"text": elapsed_str, "color": "white"},
        {"text": ")", "color": "gray"}
    ]
    send_exaroton_command(f'tellraw @a {json.dumps(msg_json)}')

def sync_and_reload():
    push_cmd = ["python3", os.path.join(os.path.dirname(__file__), "sync.py"), "push", "Shopkeepers/data/save.yml"]
    res = subprocess.run(push_cmd, capture_output=True, text=True)
    print(f"Sync Push Result: {res.stdout.strip()}")
    send_exaroton_command("shopkeeper reload")

def apply_special_sell_offer():
    with open(SAVE_YML_PATH, "r") as f:
        content = f.read()

    # 1. Remove Buy Obsidian trade (recipe 38) from General Store completely so it doesn't show up at all
    buy_obsidian_normal = """    '38':
      resultItem:
        DataVersion: 4903
        id: minecraft:obsidian
        count: 4
      item1:
        DataVersion: 4903
        id: minecraft:emerald
        count: 1\n"""

    # 2. Replace Sell Obsidian trade in Sell Drops shop (recipe 35) with 1 Obsidian -> 24 Emeralds
    sell_obsidian_normal = """    '35':
      resultItem:
        DataVersion: 4903
        id: minecraft:emerald
        count: 1
      item1:
        DataVersion: 4903
        id: minecraft:obsidian
        count: 8"""

    sell_obsidian_offer = """    '35':
      resultItem:
        DataVersion: 4903
        id: minecraft:emerald
        count: 24
      item1:
        DataVersion: 4903
        id: minecraft:obsidian
        count: 1"""

    if buy_obsidian_normal in content:
        content = content.replace(buy_obsidian_normal, "", 1)

    if sell_obsidian_normal in content:
        content = content.replace(sell_obsidian_normal, sell_obsidian_offer, 1)

    with open(SAVE_YML_PATH, "w") as f:
        f.write(content)

    print("Updated save.yml: Removed Obsidian buy trade completely & set Obsidian selling trade to 1 Obsidian = 24 Emeralds.")
    sync_and_reload()
    return True

def restore_original_trades():
    with open(SAVE_YML_PATH, "r") as f:
        content = f.read()

    buy_obsidian_normal = """    '38':
      resultItem:
        DataVersion: 4903
        id: minecraft:obsidian
        count: 4
      item1:
        DataVersion: 4903
        id: minecraft:emerald
        count: 1\n"""

    recipe_37_end = """    '37':
      resultItem:
        DataVersion: 4903
        id: minecraft:glistering_melon_slice
        count: 8
      item1:
        DataVersion: 4903
        id: minecraft:emerald
        count: 1\n"""

    sell_obsidian_offer = """    '35':
      resultItem:
        DataVersion: 4903
        id: minecraft:emerald
        count: 24
      item1:
        DataVersion: 4903
        id: minecraft:obsidian
        count: 1"""

    sell_obsidian_normal = """    '35':
      resultItem:
        DataVersion: 4903
        id: minecraft:emerald
        count: 1
      item1:
        DataVersion: 4903
        id: minecraft:obsidian
        count: 8"""

    if buy_obsidian_normal not in content and recipe_37_end in content:
        content = content.replace(recipe_37_end, recipe_37_end + buy_obsidian_normal, 1)

    if sell_obsidian_offer in content:
        content = content.replace(sell_obsidian_offer, sell_obsidian_normal, 1)

    with open(SAVE_YML_PATH, "w") as f:
        f.write(content)

    print("Restored save.yml to original trades.")
    sync_and_reload()

def broadcast_tellraw(msg):
    tellraw_cmd = f'tellraw @a {json.dumps([{"text": "[SPECIAL OFFER] ", "color": "gold", "bold": True}, {"text": msg, "color": "yellow"}])}'
    send_exaroton_command(tellraw_cmd)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--undo":
        print("Reverting special offer immediately...")
        restore_original_trades()
        broadcast_tellraw("Obsidian selling offer ended! Standard shop trades restored.")
        return

    duration = 300  # 5 minutes
    interval = 10   # broadcast every 10 seconds

    apply_special_sell_offer()

    broadcast_offer_status(0, duration)

    elapsed = 0
    while elapsed < duration:
        time.sleep(interval)
        elapsed += interval
        remaining = duration - elapsed
        if remaining > 0 and elapsed % 10 == 0:
            broadcast_offer_status(elapsed, remaining)

    restore_original_trades()
    broadcast_tellraw("⏳ Obsidian 5-minute selling special offer has ENDED! Standard shop trades restored.")

if __name__ == "__main__":
    main()
