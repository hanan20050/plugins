#!/usr/bin/env python3
"""
Custom Category Master Chest Sorter (with Automatic Backup & Restoration Support)
----------------------------------------------------------------------------------
1. Automatically creates a local timestamped backup in `WorldGuard/backups/chest_backup_<timestamp>.json`
   BEFORE performing any item movement or sorting operation.
2. Orders all items into strict sub-type blocks:
   - Building Blocks (stone, cobblestone, dirt, wood, planks, slabs, stairs, concrete, etc.)
   - Ingot / Minerals / Ores (ingots, emeralds, diamonds, coal, redstone, gold, raw metals)
   - Tools & Weapons (pickaxes, axes, shovels, swords, bows, shears)
   - Armors & Gear (helmets, chestplates, leggings, boots, shields)
   - Nature & Food (apples, beef, seeds, crops, flowers, leaves, mob drops)
   - Functional & Misc (crafting tables, furnaces, beds, signs, shulker boxes, etc.)
3. Consolidates items into a single pool, merges matching stacks, and fills Chest #1 completely (all 27 slots)
   before filling Chest #2, Chest #3, etc.
4. Supports `--undo` or `--restore` command line flags to instantly revert chests to their exact original pre-sorting state!

Usage:
  python3 categorize_and_sort_chests.py
  python3 categorize_and_sort_chests.py --undo
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from sort_chest import parse_snbt, to_snbt

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

BACKUP_DIR = os.path.join(os.path.dirname(__file__), "WorldGuard", "backups")
LATEST_BACKUP_FILE = os.path.join(BACKUP_DIR, "chest_latest_backup.json")

CHEST_COORDS = [
    (1270, 67, -219), (1270, 66, -219), (1270, 65, -219),
    (1270, 67, -218), (1270, 66, -218), (1270, 65, -218),
    (1270, 67, -216), (1270, 66, -216), (1270, 65, -216),
    (1270, 67, -214), (1270, 66, -214), (1270, 65, -214)
]

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

def get_server_logs():
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/logs"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-H", f"Authorization: Bearer {TOKEN}",
        url
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        if data.get("success"):
            return data.get("data", {}).get("content", "")
    except Exception as e:
        print(f"Error reading logs: {e}")
    return ""

def create_chest_backup(chest_data_by_coord):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"chest_backup_{timestamp}.json")
    
    # Save string keys for JSON serialization
    serializable_data = {f"{x},{y},{z}": snbt for (x, y, z), snbt in chest_data_by_coord.items()}
    
    with open(backup_path, "w") as f:
        json.dump(serializable_data, f, indent=4)
    with open(LATEST_BACKUP_FILE, "w") as f:
        json.dump(serializable_data, f, indent=4)
        
    print(f"💾 Automatic Chest Backup created: '{backup_path}'")
    print(f"📌 Latest backup pointer updated in '{LATEST_BACKUP_FILE}'")

def restore_latest_backup():
    if not os.path.exists(LATEST_BACKUP_FILE):
        print("❌ No chest backup file found to restore!")
        return False
        
    print("🔄 Restoring chests from latest automatic backup file...")
    with open(LATEST_BACKUP_FILE, "r") as f:
        backup_data = json.load(f)
        
    for coord_str, snbt in backup_data.items():
        x, y, z = map(int, coord_str.split(","))
        cmd = f"data modify block {x} {y} {z} Items set value {snbt}"
        print(f"Restoring Chest ({x}, {y}, {z})...")
        send_command(cmd)
        time.sleep(0.2)
        
    print("✨ Chest restoration completed successfully!")
    return True

def classify_item_priority(item_id):
    item_id = item_id.lower().replace("minecraft:", "")
    
    # 1. Building Blocks
    if any(k in item_id for k in [
        "stone", "cobblestone", "granite", "diorite", "andesite", "deepslate",
        "planks", "log", "wood", "brick", "concrete", "terracotta", "glass",
        "stair", "slab", "wall", "fence", "door", "trapdoor", "sandstone", "basalt",
        "dirt", "gravel", "sand", "obsidian", "purpur", "prismarine", "end_stone", "netherrack"
    ]):
        return (1, "blocks", item_id)
        
    # 2. Ingots / Ores / Minerals / Valuables
    if any(k in item_id for k in [
        "ingot", "emerald", "diamond", "gold", "iron", "netherite", "copper", "coal",
        "lapis", "redstone", "quartz", "amethyst", "raw_", "nugget"
    ]):
        return (2, "ingots_ores", item_id)

    # 3. Tools & Weapons
    if any(k in item_id for k in [
        "sword", "pickaxe", "axe", "shovel", "hoe", "bow", "crossbow", "trident",
        "shears", "flint_and_steel", "fishing_rod", "spyglass"
    ]):
        return (3, "tools", item_id)

    # 4. Armor & Gear
    if any(k in item_id for k in [
        "helmet", "chestplate", "leggings", "boots", "shield", "elytra"
    ]):
        return (4, "armors", item_id)

    # 5. Nature & Food
    if any(k in item_id for k in [
        "apple", "bread", "porkchop", "beef", "chicken", "mutton", "fish", "salmon",
        "carrot", "potato", "wheat", "seed", "sapling", "flower", "leaf", "leaves",
        "sugar_cane", "bamboo", "cactus", "melon", "pumpkin", "mushroom", "bone",
        "kelp", "berry", "berries", "lily_of_the_valley", "cornflower", "feather", "leather",
        "rotten_flesh", "spider_eye", "string", "glow_ink_sac", "ink_sac"
    ]):
        return (5, "nature", item_id)

    # 6. Functional / Utility / Misc
    return (6, "misc", item_id)

def main():
    if "--undo" in sys.argv or "--restore" in sys.argv:
        restore_latest_backup()
        return

    print("📡 Requesting live data for all 12 chests...")
    for x, y, z in CHEST_COORDS:
        send_command(f"data get block {x} {y} {z} Items")
        time.sleep(0.1)

    time.sleep(2)
    logs = get_server_logs()
    lines = logs.split("\n")

    chest_snbt_by_coord = {}
    chest_parsed_by_coord = {}

    for x, y, z in CHEST_COORDS:
        coord_pattern = f"{x}, {y}, {z}"
        for line in reversed(lines):
            if coord_pattern in line and "has the following block data: " in line:
                snbt_str = line.split("has the following block data: ", 1)[1].strip()
                try:
                    parsed = parse_snbt(snbt_str)
                    if isinstance(parsed, list):
                        chest_snbt_by_coord[(x, y, z)] = snbt_str
                        chest_parsed_by_coord[(x, y, z)] = parsed
                        break
                except Exception as e:
                    print(f"Parsing error for {coord_pattern}: {e}")

    # 🔒 CREATE AUTOMATIC BACKUP BEFORE ANY MODIFICATIONS
    create_chest_backup(chest_snbt_by_coord)

    # Pool all items together
    all_raw_items = []
    for coords, items in chest_parsed_by_coord.items():
        all_raw_items.extend(items)

    print(f"📊 Collected {len(all_raw_items)} total item stacks across all 12 chests.")

    # Stack identical items together
    stacked_map = {}
    for item in all_raw_items:
        if not isinstance(item, dict) or "id" not in item:
            continue
        item_id = item["id"]
        count = int(item.get("count", 1))
        components = item.get("components")
        
        key = (item_id, json.dumps(components, sort_keys=True) if components else "")
        if key not in stacked_map:
            stacked_map[key] = {
                "id": item_id,
                "count": 0,
                "components": components
            }
        stacked_map[key]["count"] += count

    # Split into max 64 stack sizes
    pool = []
    for (item_id, comp_str), data in stacked_map.items():
        total = data["count"]
        p_tier, cat_name, _ = classify_item_priority(item_id)
        max_s = 1 if p_tier in [3, 4] else 64
        
        while total > 0:
            take = min(total, max_s)
            entry = {"id": item_id, "count": take}
            if data["components"]:
                entry["components"] = data["components"]
            pool.append(entry)
            total -= take

    # Sort pool strictly by Category Priority 1..6, then Item ID
    pool.sort(key=lambda x: (classify_item_priority(x["id"])[0], classify_item_priority(x["id"])[2], -x["count"]))

    print(f"📦 Arranging {len(pool)} item stacks in sequence into Chest #1, Chest #2, etc...")

    # Distribute stream 27 slots at a time into Chests 0..11 sequentially
    for idx, (x, y, z) in enumerate(CHEST_COORDS):
        chest_items = pool[idx*27 : (idx+1)*27]
        slots = []
        for slot_i, item in enumerate(chest_items):
            item_copy = dict(item)
            item_copy["Slot"] = slot_i
            slots.append(item_copy)
        
        snbt_str = to_snbt(slots)
        cmd = f"data modify block {x} {y} {z} Items set value {snbt_str}"
        print(f"✨ Filling Chest #{idx+1} ({x}, {y}, {z}) with {len(slots)} items...")
        res = send_command(cmd)
        print(f"   Status: {res.strip()}")
        time.sleep(0.25)

    print("🎉 Chest Categorization & Ordering Complete with Full Automatic Backup!")

if __name__ == "__main__":
    main()
