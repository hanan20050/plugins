#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import time
import re

# Load environment variables from .env
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "admin/.env")
if not os.path.exists(ENV_FILE):
    ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if not os.path.exists(ENV_FILE):
    ENV_FILE = ".env"

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
    print("Error: EXAROTON_TOKEN or EXAROTON_SERVER_ID not found.")
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
        if key_name == "Slot":
            return f"{val}b"
        return f"{val}"
    return str(val)

def fetch_data_with_retry(command, pattern, max_attempts=6):
    send_command(command)
    for attempt in range(max_attempts):
        time.sleep(1.5)
        logs = get_logs()
        for line in reversed(logs.splitlines()):
            m = re.search(pattern, line)
            if m:
                return m.group(1)
    return None

def main():
    print("Initiating transfer of Rayan's inventory to chest at 1307 80 -238...")
    
    # 1. Fetch inventory
    player_name = "NightmareDady"
    inv_match = fetch_data_with_retry(
        f"data get entity {player_name} Inventory",
        rf"{player_name}\s+has\s+the\s+following\s+entity\s+data:\s*(\[.*\])"
    )
    
    if not inv_match:
        player_name = ".NightmareDady"
        inv_match = fetch_data_with_retry(
            f"data get entity {player_name} Inventory",
            rf"\.NightmareDady\s+has\s+the\s+following\s+entity\s+data:\s*(\[.*\])"
        )
        
    if not inv_match:
        print("Error: Could not retrieve inventory for NightmareDady or .NightmareDady.")
        sys.exit(1)
        
    # 2. Fetch chest
    chest_match = fetch_data_with_retry(
        "data get block 1307 80 -238",
        r"1307,\s*80,\s*-238\s+has\s+the\s+following\s+block\s+data:\s*(\{.*\})"
    )
    
    if not chest_match:
        print("Error: Could not retrieve chest data at 1307 80 -238.")
        sys.exit(1)

    print("Successfully retrieved player inventory and chest NBT.")
    
    # Save a backup of the original state for Undo/Rollback requirement
    backup_file = "scripts/admin/backup_transfer_inventory.json"
    backup_data = {
        "player": player_name,
        "chest_coords": [1307, 80, -238],
        "original_player_inventory": inv_match,
        "original_chest_data": chest_match
    }
    with open(backup_file, "w") as f:
        json.dump(backup_data, f, indent=4)
    print(f"Backup saved to {backup_file}")

    player_inv = parse_snbt(inv_match)
    chest_data = parse_snbt(chest_match)
    
    # Filter/map player inventory items (only copy main inventory/hotbar items, slots 0-35)
    items_to_transfer = []
    for it in player_inv:
        slot = it.get("Slot")
        # Standard inventory is slots 0-35
        if slot >= 0 and slot <= 35:
            items_to_transfer.append(it)
        
    print(f"Found {len(items_to_transfer)} items in {player_name}'s inventory.")
    
    # Place them in the chest starting from slot 0
    new_chest_items = []
    for idx, it in enumerate(items_to_transfer):
        item_copy = dict(it)
        item_copy["Slot"] = idx
        new_chest_items.append(item_copy)
        
    new_chest_snbt = to_snbt(new_chest_items)
    
    # Write to chest
    chest_cmd = f"data modify block 1307 80 -238 Items set value {new_chest_snbt}"
    print(f"Executing: {chest_cmd}")
    send_command(chest_cmd)
    
    # Clear player inventory main slots (0-35)
    # Note: clear command clears everything unless we specify target, but in Bedrock/Java we can do:
    # clear <player> to clear all inventory (which includes hotbar and main inventory, but keeps armor/offhand in modern Java edition).
    # To be extremely clean, we run clear <player>
    clear_cmd = f"clear {player_name}"
    print(f"Executing: {clear_cmd}")
    send_command(clear_cmd)
    
    print("Transfer completed! Running verification command...")
    time.sleep(2)
    send_command("data get block 1307 80 -238")
    
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--undo":
        backup_file = "scripts/admin/backup_transfer_inventory.json"
        if not os.path.exists(backup_file):
            print("No backup file found to undo.")
            sys.exit(1)
        with open(backup_file, "r") as f:
            backup_data = json.load(f)
        
        player_name = backup_data["player"]
        original_player_inventory = backup_data["original_player_inventory"]
        original_chest_data = backup_data["original_chest_data"]
        
        print("Undoing transfer...")
        chest_data_parsed = parse_snbt(original_chest_data)
        original_chest_items = chest_data_parsed.get("Items", [])
        chest_snbt = to_snbt(original_chest_items)
        send_command(f"data modify block 1307 80 -238 Items set value {chest_snbt}")
        
        player_inv_parsed = parse_snbt(original_player_inventory)
        player_snbt = to_snbt(player_inv_parsed)
        send_command(f"clear {player_name}")
        send_command(f"data modify entity {player_name} Inventory set value {player_snbt}")
        
        print("Undo completed successfully.")
        sys.exit(0)
        
    main()
