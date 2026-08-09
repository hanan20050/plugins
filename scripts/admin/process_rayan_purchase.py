#!/usr/bin/env python3
import os
import sys
import json
import re
import time
import subprocess
import uuid

# Currency values
CURRENCY_VALUES = {
    "minecraft:emerald": 1,
    "minecraft:emerald_block": 9,
    "minecraft:netherite_ingot": 64,
    "minecraft:netherite_block": 576
}

# Materials to deliver
ITEMS_TO_GIVE = [
    ("minecraft:white_concrete", 1023),
    ("minecraft:cyan_terracotta", 135),
    ("minecraft:smooth_quartz_slab", 80),
    ("minecraft:black_stained_glass_pane", 77),
    ("minecraft:smooth_quartz_stairs", 69),
    ("minecraft:glass_pane", 45),
    ("minecraft:grass_block", 42),
    ("minecraft:lantern", 36),
    ("minecraft:smooth_quartz", 31),
    ("minecraft:dirt", 30),
    ("minecraft:oak_stairs", 29),
    ("minecraft:oak_leaves", 24),
    ("minecraft:bookshelf", 23),
    ("minecraft:barrel", 17),
    ("minecraft:chest", 15),
    ("minecraft:short_grass", 15),
    ("minecraft:oak_fence", 15),
    ("minecraft:light_gray_carpet", 14),
    ("minecraft:red_carpet", 12),
    ("minecraft:dead_bush", 12),
    ("minecraft:campfire", 12),
    ("minecraft:tall_grass", 10),
    ("minecraft:oak_door", 10),
    ("minecraft:magenta_carpet", 10),
    ("minecraft:oak_slab", 10),
    ("minecraft:warped_stairs", 9),
    ("minecraft:white_carpet", 9),
    ("minecraft:gray_concrete", 8),
    ("minecraft:white_stained_glass_pane", 8),
    ("minecraft:black_concrete", 8),
    ("minecraft:polished_blackstone_stairs", 6),
    ("minecraft:furnace", 5),
    ("minecraft:blast_furnace", 5),
    ("minecraft:smoker", 5),
    ("minecraft:white_banner", 4),
    ("minecraft:red_bed", 4),
    ("minecraft:lever", 3),
    ("minecraft:end_rod", 3),
    ("minecraft:sea_pickle", 3),
    ("minecraft:crimson_stairs", 3),
    ("minecraft:oak_sign", 3),
    ("minecraft:dandelion", 2),
    ("minecraft:poppy", 2),
    ("minecraft:iron_bars", 2),
    ("minecraft:black_carpet", 2),
    ("minecraft:beehive", 2),
    ("minecraft:flowering_azalea_leaves", 1),
    ("minecraft:stonecutter", 1),
    ("minecraft:fletching_table", 1),
    ("minecraft:cartography_table", 1),
    ("minecraft:loom", 1),
    ("minecraft:smithing_table", 1),
    ("minecraft:sea_lantern", 1),
    ("minecraft:crafting_table", 1),
    ("minecraft:warped_fungus", 1),
    ("minecraft:brewing_stand", 1),
    ("minecraft:dark_oak_sapling", 1),
    ("minecraft:enchanting_table", 1),
    ("minecraft:chiseled_bookshelf", 1),
    ("minecraft:polished_blackstone_slab", 1),
    ("minecraft:grindstone", 1),
    ("minecraft:cactus", 1),
    ("minecraft:anvil", 1),
    ("minecraft:crimson_fungus", 1),
    ("minecraft:blue_orchid", 1),
    ("minecraft:acacia_button", 1),
    ("minecraft:heavy_weighted_pressure_plate", 1),
    ("minecraft:allium", 1),
    ("minecraft:ender_chest", 1),
    ("minecraft:birch_sapling", 1),
    ("minecraft:azure_bluet", 1),
    ("minecraft:cornflower", 1),
    ("minecraft:fern", 1)
]

ENV_FILE = "/Users/hanansaleh/Downloads/plugins/.env"
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
    
    # Retry loop for rate limits or transient errors
    for attempt in range(5):
        res = subprocess.run(curl_cmd, capture_output=True, text=True)
        try:
            resp_data = json.loads(res.stdout)
            if resp_data.get("success"):
                time.sleep(0.3)  # Gentle delay to prevent rate limits
                return resp_data
            else:
                print(f"API returned error: {resp_data.get('error')}. Retrying in 2s...")
        except Exception as e:
            # Check for HTTP rate limits (429) or other errors in headers
            print(f"Curl command failed or returned non-JSON. Retrying in 2s... Error: {e}")
        time.sleep(2)
        
    print(f"FAILED to execute command after 5 attempts: {cmd}")
    return None

def fetch_logs():
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/logs"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "GET", url,
        "-H", f"Authorization: Bearer {TOKEN}"
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        if data.get("success"):
            return data.get("data", {}).get("content", "")
    except Exception as e:
        print(f"Error parsing logs: {e}")
    return ""

def execute_and_get_output(cmd):
    token = str(uuid.uuid4())[:8]
    send_command(f"say START_{token}")
    send_command(cmd)
    send_command(f"say END_{token}")
    
    time.sleep(12)
    logs = fetch_logs()
    lines = logs.split("\n")
    
    output_lines = []
    started = False
    for line in lines:
        if f"START_{token}" in line:
            started = True
            continue
        if f"END_{token}" in line:
            break
        if started:
            if "issued server command:" in line and cmd in line:
                continue
            output_lines.append(line)
    return output_lines

def parse_snbt(s):
    tokens = []
    i = 0
    while i < len(s):
        c = s[i]
        if c in " \t\r\n":
            i += 1
            continue
        if c in "{}[],:":
            tokens.append((c, c))
            i += 1
            continue
        if c == '"':
            i += 1
            val = []
            while i < len(s):
                if s[i] == '\\' and i + 1 < len(s):
                    val.append(s[i+1])
                    i += 2
                elif s[i] == '"':
                    break
                else:
                    val.append(s[i])
                    i += 1
            tokens.append(("STRING", "".join(val)))
            i += 1
            continue
        start = i
        while i < len(s):
            if s[i] in " \t\r\n{}[],:\"":
                break
            i += 1
        raw = s[start:i]
        if re.match(r"^-?\d+[bslfdb]?$", raw, re.I):
            tokens.append(("NUM", raw))
        else:
            tokens.append(("IDENT", raw))
            
    idx = 0
    def parse_value():
        nonlocal idx
        if idx >= len(tokens): return None
        t, v = tokens[idx]
        if t == "{":
            idx += 1
            obj = {}
            while idx < len(tokens) and tokens[idx][0] != "}":
                kt, kv = tokens[idx]
                idx += 1
                if idx < len(tokens) and tokens[idx][0] == ":":
                    idx += 1
                vv = parse_value()
                obj[kv] = vv
                if idx < len(tokens) and tokens[idx][0] == ",":
                    idx += 1
            if idx < len(tokens) and tokens[idx][0] == "}":
                idx += 1
            return obj
        elif t == "[":
            idx += 1
            lst = []
            while idx < len(tokens) and tokens[idx][0] != "]":
                vv = parse_value()
                if vv is not None: lst.append(vv)
                if idx < len(tokens) and tokens[idx][0] == ",":
                    idx += 1
            if idx < len(tokens) and tokens[idx][0] == "]":
                idx += 1
            return lst
        else:
            idx += 1
            if t == "NUM":
                clean_num = re.sub(r"[bslfdb]$", "", v, flags=re.I)
                try:
                    if "." in clean_num:
                        return float(clean_num)
                    return int(clean_num)
                except ValueError:
                    return clean_num
            return v
    return parse_value()

def get_player_inventory(player_name):
    out = execute_and_get_output(f"data get entity {player_name} Inventory")
    for line in out:
        if "entity data:" in line:
            m = re.search(r"entity data:\s*(\[.*\])", line)
            if m:
                return parse_snbt(m.group(1))
    return None

def get_chest_inventory(x, y, z):
    out = execute_and_get_output(f"data get block {x} {y} {z} Items")
    for line in out:
        if "block data:" in line:
            m = re.search(r"block data:\s*(\[.*\])", line)
            if m:
                return parse_snbt(m.group(1))
    return []

def calculate_balance(inventory):
    if not inventory:
        return 0, {}
    counts = {k: 0 for k in CURRENCY_VALUES.keys()}
    for item in inventory:
        item_id = item.get("id")
        if item_id in CURRENCY_VALUES:
            slot_raw = item.get("Slot") if "Slot" in item else item.get("slot", 0)
            slot = int(re.sub(r"[^\d-]", "", str(slot_raw)))
            if -106 <= slot <= 35:
                count_raw = item.get("Count") if "Count" in item else item.get("count", 1)
                count = int(re.sub(r"[^\d]", "", str(count_raw)))
                counts[item_id] += count
                
    total_val = sum(counts[k] * CURRENCY_VALUES[k] for k in counts)
    return total_val, counts

def find_optimal_payment(counts, target):
    best_combo = None
    min_value = float('inf')
    
    nb_max = counts.get("minecraft:netherite_block", 0)
    ni_max = counts.get("minecraft:netherite_ingot", 0)
    eb_max = counts.get("minecraft:emerald_block", 0)
    e_max = counts.get("minecraft:emerald", 0)
    
    for nb in range(nb_max + 1):
        for ni in range(ni_max + 1):
            for eb in range(eb_max + 1):
                for e in range(e_max + 1):
                    val = nb * 576 + ni * 64 + eb * 9 + e * 1
                    if val >= target:
                        if val < min_value:
                            min_value = val
                            best_combo = (nb, ni, eb, e)
    return best_combo, min_value

def check_online_players():
    out = execute_and_get_output("list")
    for line in out:
        if "online" in line.lower() or "players" in line.lower() or "default" in line.lower():
            if "NightmareDady" in line:
                return True
    return False

def main():
    player = "NightmareDady"
    chest_coords = (1307, 80, -238)
    cost = 1315
    
    print(f"Starting payment processing loop for {player}...")
    
    while True:
        if not check_online_players():
            print(f"{player} is offline. Waiting 20 seconds...")
            time.sleep(20)
            continue
            
        inv = get_player_inventory(player)
        if inv is None:
            print(f"Could not retrieve inventory for {player}. Waiting 15 seconds...")
            time.sleep(15)
            continue
            
        balance, counts = calculate_balance(inv)
        print(f"Player Balance: {balance} Emeralds. Details: {counts}")
        
        if balance < cost:
            send_command(f"msg {player} §c[Shop] You do not have enough money! Needed: {cost} Emeralds. Your Balance: {balance} Emeralds. Please load funds.")
            print(f"Balance too low. Waiting 20 seconds...")
            time.sleep(20)
            continue
            
        combo, total_paid = find_optimal_payment(counts, cost)
        if not combo:
            print("Error: Could not find valid payment combination despite high balance.")
            time.sleep(20)
            continue
            
        print(f"Optimal payment combination: {combo} (Total: {total_paid} Emeralds)")
        
        # Deduct
        nb, ni, eb, e = combo
        if nb > 0: send_command(f"clear {player} minecraft:netherite_block {nb}")
        if ni > 0: send_command(f"clear {player} minecraft:netherite_ingot {ni}")
        if eb > 0: send_command(f"clear {player} minecraft:emerald_block {eb}")
        if e > 0: send_command(f"clear {player} minecraft:emerald {e}")
        
        # Return change
        change = total_paid - cost
        if change > 0:
            print(f"Returning change: {change} Emeralds")
            change_nb = change // 576
            change %= 576
            change_ni = change // 64
            change %= 64
            change_eb = change // 9
            change %= 9
            change_e = change
            
            if change_nb > 0: send_command(f"give {player} minecraft:netherite_block {change_nb}")
            if change_ni > 0: send_command(f"give {player} minecraft:netherite_ingot {change_ni}")
            if change_eb > 0: send_command(f"give {player} minecraft:emerald_block {change_eb}")
            if change_e > 0: send_command(f"give {player} minecraft:emerald {change_e}")
            
        send_command(f"msg {player} §a[Shop] Payment of {cost} Emeralds confirmed! Initiating delivery of schematic materials...")
        break
        
    # --- Material Delivery ---
    send_command(f"setblock {chest_coords[0]} {chest_coords[1]} {chest_coords[2]} minecraft:chest keep")
    
    stacks_to_deliver = []
    for item_id, total_count in ITEMS_TO_GIVE:
        while total_count > 0:
            count = min(total_count, 64)
            stacks_to_deliver.append((item_id, count))
            total_count -= count
            
    print(f"Delivering {len(stacks_to_deliver)} stacks of items...")
    
    # Query inventory again
    inv = get_player_inventory(player)
    occupied_slots = set()
    if inv:
        for item in inv:
            slot_raw = item.get("Slot") if "Slot" in item else item.get("slot")
            if slot_raw is not None:
                slot = int(re.sub(r"[^\d-]", "", str(slot_raw)))
                if 0 <= slot <= 35:
                    occupied_slots.add(slot)
    free_inv_slots = [s for s in range(36) if s not in occupied_slots]
    print(f"Free inventory slots: {len(free_inv_slots)}")
    
    chest_items = get_chest_inventory(*chest_coords)
    occupied_chest_slots = set()
    if chest_items:
        for item in chest_items:
            slot_raw = item.get("Slot") if "Slot" in item else item.get("slot")
            if slot_raw is not None:
                slot = int(re.sub(r"[^\d-]", "", str(slot_raw)))
                if 0 <= slot <= 26:
                    occupied_chest_slots.add(slot)
    free_chest_slots = [s for s in range(27) if s not in occupied_chest_slots]
    print(f"Free chest slots: {len(free_chest_slots)}")
    
    for item_id, count in stacks_to_deliver:
        if free_inv_slots:
            free_inv_slots.pop(0)
            send_command(f"give {player} {item_id} {count}")
        elif free_chest_slots:
            slot = free_chest_slots.pop(0)
            send_command(f"item replace block {chest_coords[0]} {chest_coords[1]} {chest_coords[2]} container.{slot} with {item_id} {count}")
        else:
            send_command(f"execute at {player} run summon minecraft:item ~ ~ ~ {{Item:{{id:\"{item_id}\",Count:{count}b}}}}")
            
    send_command(f"msg {player} §a[Shop] Material delivery complete! Any items that did not fit in your inventory or the chest at ({chest_coords[0]}, {chest_coords[1]}, {chest_coords[2]}) have been dropped near you.")
    print("✅ All processes completed successfully.")

if __name__ == '__main__':
    main()
