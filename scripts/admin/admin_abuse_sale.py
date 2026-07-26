#!/usr/bin/env python3
"""
Admin Abuse Shop Sale Script
- Temporarily modifies Shopkeepers 1, 2, 6, and 7 (Buying Shops: General Store, Land Upgrades, Enchanted Books, Biome Coordinates) in save.yml.
- Sets the cost (item1) of all trades in these shops to 50% of their original price.
- Backs up save.yml before starting, and restores the original save.yml after 1.5 minutes (90 seconds).
- Broadcasts tellraw notifications to all players every 10 seconds with a live timer.
- Pushes save.yml to the Exaroton server and reloads the Shopkeepers plugin on start, update, and end.
- Supports --undo to immediately restore original trades and cancel any active sale.
"""

import os
import sys
import json
import time
import subprocess
import re

PLUGINS_DIR = "/Users/hanansaleh/Downloads/plugins"
SAVE_YML_PATH = os.path.join(PLUGINS_DIR, "Shopkeepers", "data", "save.yml")
BACKUP_YML_PATH = os.path.join(PLUGINS_DIR, "Shopkeepers", "data", "save.yml.bak_abuse_pre")
SYNC_PY_PATH = os.path.join(PLUGINS_DIR, "sync.py")

# Load environment variables from .env
ENV_FILE = os.path.join(PLUGINS_DIR, ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()

HARDCODED_TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
HARDCODED_SERVER_ID = "cEuS61sZvNEFS3aB"

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or HARDCODED_TOKEN
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or HARDCODED_SERVER_ID

# Target only the buying shops, excluding Money Exchange (5) and Sell Drops (4)
ELIGIBLE_SHOPS = ["1", "2", "6", "7"]

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

def broadcast_tellraw(msg_json):
    send_exaroton_command(f'tellraw @a {json.dumps(msg_json)}')

def sync_and_reload():
    push_cmd = ["python3", SYNC_PY_PATH, "push", "Shopkeepers/data/save.yml", "--force"]
    res = subprocess.run(push_cmd, capture_output=True, text=True)
    print(f"Sync Push Result: {res.stdout.strip()}")
    send_exaroton_command("shopkeeper reload")

def get_original_value(item_id, count):
    if item_id == "minecraft:emerald":
        return count
    elif item_id == "minecraft:emerald_block":
        return count * 9
    elif item_id == "minecraft:netherite_ingot":
        return count * 64
    elif item_id == "minecraft:netherite_block":
        return count * 576
    else:
        return count

def value_to_currency(emeralds, original_id):
    if emeralds >= 576 and emeralds % 576 == 0:
        return "minecraft:netherite_block", emeralds // 576
    elif emeralds >= 64 and emeralds % 64 == 0:
        return "minecraft:netherite_ingot", emeralds // 64
    elif emeralds >= 9 and emeralds % 9 == 0:
        return "minecraft:emerald_block", emeralds // 9
    else:
        return "minecraft:emerald", emeralds

def discount_item(item_id, count):
    currencies = ["minecraft:emerald", "minecraft:emerald_block", "minecraft:netherite_ingot", "minecraft:netherite_block"]
    if item_id in currencies:
        val = get_original_value(item_id, count)
        discounted_val = max(1, round(val * 0.5))
        return value_to_currency(discounted_val, item_id)
    else:
        discounted_count = max(1, round(count * 0.5))
        return item_id, discounted_count

def apply_abuse_sale():
    if not os.path.exists(SAVE_YML_PATH):
        print(f"Error: {SAVE_YML_PATH} does not exist.")
        return False

    # Backup the original file
    with open(SAVE_YML_PATH, "r") as f:
        original_content = f.read()

    with open(BACKUP_YML_PATH, "w") as f:
        f.write(original_content)
    print(f"Backup created at {BACKUP_YML_PATH}")

    # Process and modify eligible shops trades
    lines = original_content.splitlines()
    
    current_shop = None
    current_recipe_id = None
    item1_id = None
    item1_count = None
    item1_id_line_idx = None
    item1_count_line_idx = None
    
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        
        # Detect start of a shopkeeper block
        shop_match = re.match(r"^'(\d+)':", line)
        if shop_match:
            current_shop = shop_match.group(1)
            current_recipe_id = None

        if current_shop in ELIGIBLE_SHOPS:
            # Detect a recipe start
            match = re.match(r"^ {4}'(\d+)':", line)
            if match:
                current_recipe_id = match.group(1)
                item1_id = None
                item1_count = None
                item1_id_line_idx = None
                item1_count_line_idx = None
            
            # Detect item1 properties
            if current_recipe_id:
                if stripped == "item1:":
                    # Look ahead to find id and count
                    look_idx = idx + 1
                    while look_idx < len(lines):
                        look_line = lines[look_idx]
                        look_stripped = look_line.strip()
                        look_spaces = len(look_line) - len(look_line.lstrip())
                        if look_spaces <= 6 and look_stripped:
                            break
                        
                        if look_stripped.startswith("id:"):
                            item1_id = look_stripped.split(":", 1)[1].strip()
                            item1_id_line_idx = look_idx
                        elif look_stripped.startswith("count:"):
                            item1_count = int(look_stripped.split(":", 1)[1].strip())
                            item1_count_line_idx = look_idx
                        
                        look_idx += 1
                    
                    if item1_id and item1_count is not None:
                        new_id, new_count = discount_item(item1_id, item1_count)
                        id_spaces = len(lines[item1_id_line_idx]) - len(lines[item1_id_line_idx].lstrip())
                        count_spaces = len(lines[item1_count_line_idx]) - len(lines[item1_count_line_idx].lstrip())
                        lines[item1_id_line_idx] = " " * id_spaces + f"id: {new_id}"
                        lines[item1_count_line_idx] = " " * count_spaces + f"count: {new_count}"
                        current_recipe_id = None

        idx += 1

    with open(SAVE_YML_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Successfully modified save.yml for Admin Abuse 50% Off Sale on shops: {ELIGIBLE_SHOPS}.")
    sync_and_reload()
    return True

def restore_original_trades():
    if not os.path.exists(BACKUP_YML_PATH):
        print("Warning: No backup file found. Cannot restore.")
        return False

    with open(BACKUP_YML_PATH, "r") as f:
        original_content = f.read()

    with open(SAVE_YML_PATH, "w") as f:
        f.write(original_content)

    print("Restored original save.yml.")
    sync_and_reload()
    
    try:
        os.remove(BACKUP_YML_PATH)
        print("Removed backup file.")
    except OSError as e:
        print(f"Error removing backup file: {e}")
        
    return True

def broadcast_sale_status(elapsed, remaining):
    mins_rem, secs_rem = divmod(remaining, 60)
    time_str = f"{mins_rem}m {secs_rem}s" if mins_rem > 0 else f"{secs_rem}s"
    mins_el, secs_el = divmod(elapsed, 60)
    elapsed_str = f"{mins_el}m {secs_el}s" if mins_el > 0 else f"{secs_el}s"

    msg_json = [
        {"text": "⚠ [ADMIN ABUSE SALE] ⚠ ", "color": "red", "bold": True},
        {"text": "Everything in ALL Buying Shops is ", "color": "yellow"},
        {"text": "50% OFF", "color": "green", "bold": True},
        {"text": "! | Remaining: ", "color": "aqua"},
        {"text": time_str, "color": "red", "bold": True},
        {"text": " (Passed: ", "color": "gray"},
        {"text": elapsed_str, "color": "white"},
        {"text": ")", "color": "gray"}
    ]
    broadcast_tellraw(msg_json)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--undo":
        print("Reverting admin abuse sale immediately...")
        if restore_original_trades():
            msg_json = [
                {"text": "⏳ [ADMIN ABUSE SALE] ", "color": "red", "bold": True},
                {"text": "Sale has been cancelled/ended! Standard shop prices restored.", "color": "yellow"}
            ]
            broadcast_tellraw(msg_json)
        return

    duration = 90  # 1.5 minutes
    interval = 10  # broadcast every 10 seconds

    print("Starting Admin Abuse 50% Off Sale...")
    if not apply_abuse_sale():
        print("Failed to apply sale.")
        return

    # Broadcast initial message
    msg_json_start = [
        {"text": "⚠ [ADMIN ABUSE SALE] ⚠ ", "color": "red", "bold": True},
        {"text": "Everything in ALL Buying Shops is now ", "color": "yellow"},
        {"text": "50% OFF", "color": "green", "bold": True},
        {"text": " for the next ", "color": "yellow"},
        {"text": "1.5 minutes", "color": "aqua", "bold": True},
        {"text": "! Go go go!", "color": "yellow"}
    ]
    broadcast_tellraw(msg_json_start)
    broadcast_sale_status(0, duration)

    elapsed = 0
    while elapsed < duration:
        time.sleep(interval)
        elapsed += interval
        remaining = duration - elapsed
        if remaining > 0:
            broadcast_sale_status(elapsed, remaining)

    print("Ending Admin Abuse Sale...")
    restore_original_trades()
    
    msg_json_end = [
        {"text": "⏳ [ADMIN ABUSE SALE] ", "color": "red", "bold": True},
        {"text": "Admin Abuse Sale has ended! Standard shop prices restored to normal.", "color": "yellow"}
    ]
    broadcast_tellraw(msg_json_end)

if __name__ == "__main__":
    main()
