#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import time
import re
import uuid

# Load environment variables from .env
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    CONFIG[parts[0].strip()] = parts[1].strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID")

if not TOKEN or not SERVER_ID:
    print("Error: EXAROTON_TOKEN or EXAROTON_SERVER_ID not found in .env or environment variables.")
    sys.exit(1)

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

def get_logs():
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/logs"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-H", f"Authorization: Bearer {TOKEN}"
    ]
    res = subprocess.run(curl_cmd + [url], capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        if data.get("success"):
            return data.get("data", {}).get("content", "")
    except Exception as e:
        print(f"Error parsing log response: {e}")
    return ""

def parse_snbt(s):
    # Lexer
    tokens = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in "{}[],:":
            tokens.append((c, c))
            i += 1
        elif c == '"' or c == "'":
            quote = c
            start = i
            i += 1
            escaped = False
            while i < n:
                if s[i] == quote and not escaped:
                    i += 1
                    break
                if s[i] == '\\':
                    escaped = not escaped
                else:
                    escaped = False
                i += 1
            tokens.append(("STRING", s[start+1:i-1].replace('\\' + quote, quote)))
        else:
            start = i
            while i < n and s[i] not in "{}[],: \t\r\n\"'":
                i += 1
            val = s[start:i]
            if val.lower().endswith(('b', 's', 'l', 'f', 'd')) and val[:-1].lstrip('-').replace('.', '', 1).isdigit():
                tokens.append(("NUMBER", val))
            elif val.lstrip('-').replace('.', '', 1).isdigit():
                tokens.append(("NUMBER", val))
            elif val == "true" or val == "false":
                tokens.append(("BOOL", val))
            else:
                tokens.append(("IDENT", val))
                
    # Parser
    idx = 0
    def peek():
        nonlocal idx
        return tokens[idx] if idx < len(tokens) else (None, None)
        
    def consume(expected_type=None):
        nonlocal idx
        t, val = tokens[idx]
        idx += 1
        return val

    def parse_value():
        t, val = peek()
        if t == "{":
            return parse_dict()
        elif t == "[":
            return parse_list()
        elif t == "STRING":
            consume()
            return val
        elif t == "NUMBER":
            consume()
            suffix = val[-1].lower()
            if suffix in ('b', 's', 'l', 'f', 'd') and len(val) > 1 and val[:-1].lstrip('-').replace('.', '', 1).isdigit():
                num_str = val[:-1]
            else:
                num_str = val
                suffix = None
            if '.' in num_str:
                return float(num_str)
            else:
                return int(num_str)
        elif t == "BOOL":
            consume()
            return val == "true"
        elif t == "IDENT":
            consume()
            return val
        else:
            raise ValueError(f"Unexpected token: {t} ({val})")

    def parse_dict():
        consume("{")
        res = {}
        while True:
            t, val = peek()
            if t == "}":
                consume("}")
                break
            key = consume()
            consume(":")
            val = parse_value()
            res[key] = val
            t, val = peek()
            if t == ",":
                consume(",")
            elif t == "}":
                pass
            else:
                raise ValueError(f"Expected , or }} but got {t}")
        return res

    def parse_list():
        consume("[")
        t, val = peek()
        if t == "IDENT" and idx + 1 < len(tokens) and tokens[idx+1][0] == ";":
            consume()
            consume(";")
        res = []
        while True:
            t, val = peek()
            if t == "]":
                consume("]")
                break
            val = parse_value()
            res.append(val)
            t, val = peek()
            if t == ",":
                consume(",")
            elif t == "]":
                pass
            else:
                raise ValueError(f"Expected , or ] but got {t}")
        return res

    return parse_value()

def to_snbt(val, key_name=None):
    if isinstance(val, dict):
        parts = []
        for k, v in val.items():
            quoted_key = f'"{k}"'
            parts.append(f"{quoted_key}: {to_snbt(v, k)}")
        return "{" + ", ".join(parts) + "}"
    elif isinstance(val, list):
        return "[" + ", ".join(to_snbt(x) for x in val) + "]"
    elif isinstance(val, bool):
        return "1b" if val else "0b"
    elif isinstance(val, str):
        escaped = val.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    elif isinstance(val, int):
        if key_name == "Slot" or key_name == "bold":
            return f"{val}b"
        return f"{val}"
    return str(val)

def get_max_stack_size(item_id):
    non_stackable = [
        "_sword", "_pickaxe", "_axe", "_shovel", "_hoe", "_helmet", "_chestplate", 
        "_leggings", "_boots", "bow", "shield", "elytra", "totem_of_undying", 
        "potion", "written_book", "writable_book", "spear", "flint_and_steel"
    ]
    for ns in non_stackable:
        if ns in item_id:
            return 1
    
    stackable_16 = ["egg", "ender_pearl", "snowball", "bucket", "sign", "banner"]
    for s16 in stackable_16:
        if s16 in item_id:
            return 16
            
    return 64

def get_item_category(item_id):
    # 1. Weapons, tools, armor
    tool_indicators = [
        "_sword", "_pickaxe", "_axe", "_shovel", "_hoe", 
        "_helmet", "_chestplate", "_leggings", "_boots", 
        "bow", "shield", "shears", "flint_and_steel", 
        "fishing_rod", "trident", "brush", "spyglass", "elytra", "spear"
    ]
    for indicator in tool_indicators:
        if indicator in item_id:
            return "tool"
            
    # 2. Farming, food, plants, seeds, nature
    farming_indicators = [
        "seed", "sapling", "flower", "rose", "dandelion", "poppy", "orchid", "allium", "bluet",
        "tulip", "daisy", "button", "lilac", "peony", "sunflower", "bush", "grass", "fern",
        "leaves", "leaf", "apple", "carrot", "potato", "bread", "wheat", "melon", "pumpkin",
        "sugar", "chicken", "beef", "porkchop", "mutton", "rabbit", "fish", "salmon", "cod",
        "cookie", "pie", "stew", "soup", "mushroom", "berries", "kelp", "bamboo", "vine"
    ]
    for indicator in farming_indicators:
        if indicator in item_id:
            return "farming"

    # 3. Blocks & building resources (dirt, stone, sand, planks, etc.)
    block_indicators = [
        "dirt", "stone", "cobblestone", "sand", "gravel", "granite", "diorite", "andesite",
        "deepslate", "tuff", "obsidian", "netherrack", "end_stone", "prismarine", "purpur",
        "wool", "glass", "clay", "terracotta", "concrete", "planks", "log", "wood", "slab",
        "stairs", "fence", "gate", "door", "trapdoor", "pressure_plate", "chest", "shulker_box",
        "furnace", "crafting_table", "anvil", "beacon", "brick", "sponge", "tnt", "torch", "lantern"
    ]
    for indicator in block_indicators:
        if indicator in item_id:
            return "block"
            
    # 4. Misc items (dyes, materials, drops, etc.)
    return "misc"

def get_fresh_block_data(x, y, z):
    send_command(f"data get block {x} {y} {z}")
    pattern = rf"{x},\s*{y},\s*{z}\s+has\s+the\s+following\s+block\s+data:\s*(\{{.*\}})"
    
    for attempt in range(5):
        time.sleep(1.5)
        logs = get_logs()
        for line in reversed(logs.splitlines()):
            m = re.search(pattern, line)
            if m:
                return m.group(1)
    return None

def get_player_inventory(player_name):
    send_command(f"data get entity {player_name} Inventory")
    pattern = rf"{player_name}\s+has\s+the\s+following\s+entity\s+data:\s*(\[.*\])"
    
    for attempt in range(5):
        time.sleep(1.5)
        logs = get_logs()
        for line in reversed(logs.splitlines()):
            m = re.search(pattern, line)
            if m:
                return m.group(1)
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 sort_chest.py --targets <coords_or_players> ...")
        print("Example:")
        print("  python3 sort_chest.py --targets 1296 80 -225 1296 81 -228 1295 82 -227 hanansaleh")
        sys.exit(1)

    args = sys.argv[1:]
    if args[0] == "--targets":
        args = args[1:]
        
    targets = []
    i = 0
    while i < len(args):
        val = args[i]
        # Check if coordinates (3 consecutive numbers)
        if i + 2 < len(args) and re.match(r"^-?\d+$", val) and re.match(r"^-?\d+$", args[i+1]) and re.match(r"^-?\d+$", args[i+2]):
            targets.append(("block", (args[i], args[i+1], args[i+2])))
            i += 3
        else:
            targets.append(("player", val))
            i += 1

    print(f"Target inventories: {targets}")
    
    # Retrieve all items from all targets
    all_items = []
    player_armor_offhand = {} # store player armor/offhand items to put them back exactly as they were
    
    for t_type, t_val in targets:
        if t_type == "block":
            x, y, z = t_val
            print(f"Fetching container at {x} {y} {z}...")
            match = get_fresh_block_data(x, y, z)
            if not match:
                print(f"Warning: Could not fetch data for block at {x} {y} {z}")
                continue
            block_data = parse_snbt(match)
            items = block_data.get("Items", [])
            for it in items:
                # Add source tag to trace if needed
                all_items.append(it)
        elif t_type == "player":
            print(f"Fetching player inventory for {t_val}...")
            match = get_player_inventory(t_val)
            if not match:
                print(f"Warning: Could not fetch inventory for player {t_val}")
                continue
            inv_data = parse_snbt(match)
            player_armor_offhand[t_val] = []
            for it in inv_data:
                slot = it.get("Slot")
                # Keep armor (100-103) and offhand (-106) separate
                if slot >= 100 or slot < 0:
                    player_armor_offhand[t_val].append(it)
                else:
                    all_items.append(it)

    print(f"Total raw items collected: {len(all_items)}")

    # Consolidate stackable items
    # Group by: id + components (serialized as JSON string)
    stackables = {}
    non_stackables = []
    
    for item in all_items:
        item_id = item.get("id")
        count = item.get("count", 1)
        components = item.get("components", {})
        comp_key = json.dumps(components, sort_keys=True)
        max_stack = get_max_stack_size(item_id)
        
        if max_stack > 1:
            key = (item_id, comp_key, max_stack)
            stackables[key] = stackables.get(key, 0) + count
        else:
            non_stackables.append(item)

    # Rebuild final consolidated items list
    consolidated_items = []
    for (item_id, comp_key, max_stack), total_count in stackables.items():
        components = json.loads(comp_key)
        while total_count > 0:
            take = min(total_count, max_stack)
            item_entry = {"id": item_id, "count": take}
            if components:
                item_entry["components"] = components
            consolidated_items.append(item_entry)
            total_count -= take
            
    consolidated_items.extend(non_stackables)

    # Global sorting key
    # 1. Category (tool, block, farming, misc)
    # 2. Item ID (alphabetical)
    # 3. Count (descending, so full stacks come first)
    # 4. Durability/Damage
    # 5. Component JSON
    category_priority = {"tool": 1, "block": 2, "farming": 3, "misc": 4}
    
    def get_sort_key(item):
        item_id = item.get("id", "")
        cat = get_item_category(item_id)
        priority = category_priority.get(cat, 4)
        components = item.get("components", {})
        damage = components.get("minecraft:damage", 0) if isinstance(components, dict) else 0
        comp_str = json.dumps(components, sort_keys=True)
        count = item.get("count", 1)
        return (priority, item_id, -count, damage, comp_str)

    consolidated_items.sort(key=get_sort_key)
    
    # Smart distribution of sorted items to targets
    # Let's map target containers:
    # 1. Player inventory should get:
    #    - Player's active tools (highest priority tools/weapons/armor)
    #    - Utilities: torches, leads, ladders, crafting tables, etc.
    #    - Food
    #    - Remaining slots filled with standard blocks/materials they were carrying
    # 2. Shulker box gets remaining tools, gear, and special books
    # 3. Chests get the remaining items sorted by category (farming/food/misc vs building blocks)
    
    player_targets = [t for t in targets if t[0] == "player"]
    shulker_targets = []
    chest_targets = []
    
    for t_type, t_val in targets:
        if t_type == "block":
            x, y, z = t_val
            # Probe log to find type if we want, or default to checking coordinates
            # Let's assume shulker is 1296 81 -228
            if x == "1296" and y == "81" and z == "-228":
                shulker_targets.append(t_val)
            else:
                chest_targets.append(t_val)

    # Let's classify consolidated items into groups for distribution
    player_inventory_items = []
    tool_gear_items = []
    block_items = []
    farming_misc_items = []
    
    for item in consolidated_items:
        item_id = item.get("id", "")
        cat = get_item_category(item_id)
        
        # If it's a primary player tool, keep it for player inventory
        is_primary_tool = cat == "tool" and any(x in item_id for x in ["_pickaxe", "_axe", "_shovel", "_sword", "bow", "flint_and_steel", "lead", "torch", "ladder", "crafting_table"])
        is_player_food = cat == "farming" and any(x in item_id for x in ["potato", "carrot", "bread", "beef", "chicken", "apple"])
        
        if (is_primary_tool or is_player_food) and len(player_inventory_items) < 27:
            player_inventory_items.append(item)
        elif cat == "tool" or "written_book" in item_id:
            tool_gear_items.append(item)
        elif cat == "block":
            block_items.append(item)
        else:
            farming_misc_items.append(item)

    # Fill remaining player inventory slots with some blocks they were carrying (e.g. cobblestone_stairs, planks, deepslate)
    # to avoid empty inventory if possible
    remaining_player_slots = 36 - len(player_inventory_items)
    if remaining_player_slots > 0 and block_items:
        # Move some block stacks to player inventory
        to_move = block_items[:remaining_player_slots]
        player_inventory_items.extend(to_move)
        block_items = block_items[remaining_player_slots:]

    # Now distribute the rest:
    # 1. Shulker box gets all tool_gear_items. If it overflows, overflow goes to chests.
    # 2. Chest 1 (farming/misc) gets farming_misc_items.
    # 3. Chest 2 (blocks) gets block_items.
    
    shulker_box_items = []
    chest_1_items = [] # Farming / Nature / Food / Misc
    chest_2_items = [] # Blocks / Terrain / Resources
    
    shulker_box_items.extend(tool_gear_items)
    chest_1_items.extend(farming_misc_items)
    chest_2_items.extend(block_items)
    
    # Sort each list to ensure strict consecutive layout
    player_inventory_items.sort(key=get_sort_key)
    shulker_box_items.sort(key=get_sort_key)
    chest_1_items.sort(key=get_sort_key)
    chest_2_items.sort(key=get_sort_key)

    # Let's perform writing back to the targets!
    
    # A. Write Player Inventories
    for t_type, t_val in targets:
        if t_type == "player":
            # Assign slot IDs (0-35)
            player_slots = []
            for slot_idx, item in enumerate(player_inventory_items[:36]):
                item_copy = dict(item)
                item_copy["Slot"] = slot_idx
                player_slots.append(item_copy)
            # Add back armor & offhand
            player_slots.extend(player_armor_offhand.get(t_val, []))
            
            snbt_val = to_snbt(player_slots)
            cmd = f"data modify entity {t_val} Inventory set value {snbt_val}"
            print(f"Updating player inventory for {t_val}...")
            send_command(cmd)

    # B. Write Shulker Box (1296 81 -228)
    if shulker_targets:
        shulker_coords = shulker_targets[0]
        box_slots = []
        for slot_idx, item in enumerate(shulker_box_items[:27]):
            item_copy = dict(item)
            item_copy["Slot"] = slot_idx
            box_slots.append(item_copy)
        snbt_val = to_snbt(box_slots)
        coords_str = " ".join(shulker_coords)
        cmd = f"data modify block {coords_str} Items set value {snbt_val}"
        print(f"Updating Shulker Box at {coords_str}...")
        send_command(cmd)
        
    # C. Write Chests
    # Chest 1: 1296 80 -225 (Farming/Misc)
    # Chest 2: 1295 82 -227 (Blocks)
    for coords in chest_targets:
        x, y, z = coords
        if x == "1296" and y == "80" and z == "-225":
            slots = []
            for slot_idx, item in enumerate(chest_1_items[:27]):
                item_copy = dict(item)
                item_copy["Slot"] = slot_idx
                slots.append(item_copy)
            snbt_val = to_snbt(slots)
            cmd = f"data modify block {x} {y} {z} Items set value {snbt_val}"
            print(f"Updating Farming Chest at {x} {y} {z}...")
            send_command(cmd)
        elif x == "1295" and y == "82" and z == "-227":
            slots = []
            for slot_idx, item in enumerate(chest_2_items[:27]):
                item_copy = dict(item)
                item_copy["Slot"] = slot_idx
                slots.append(item_copy)
            snbt_val = to_snbt(slots)
            cmd = f"data modify block {x} {y} {z} Items set value {snbt_val}"
            print(f"Updating Blocks Chest at {x} {y} {z}...")
            send_command(cmd)

    print("\nSorting completed successfully!")

if __name__ == "__main__":
    main()
