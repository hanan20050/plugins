#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import time

ENV_FILE = "/Users/hanansaleh/Downloads/plugins/.env"
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    CONFIG[parts[0].strip()] = parts[1].strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or "cEuS61sZvNEFS3aB"

BACKUP_FILE = "/Users/hanansaleh/Downloads/plugins/logs_and_backups/clear_wilderness_chests_backup.json"
ALL_CHESTS_FILE = "/Users/hanansaleh/Downloads/plugins/logs_and_backups/all_world_chests.json"

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

def undo():
    if not os.path.exists(BACKUP_FILE):
        print(f"Error: Backup file {BACKUP_FILE} not found. Cannot undo.")
        sys.exit(1)
        
    with open(BACKUP_FILE, "r") as f:
        backup_data = json.load(f)
        
    print(f"Undoing and restoring {len(backup_data)} wilderness chest inventories...")
    for chest in backup_data:
        x, y, z = chest["x"], chest["y"], chest["z"]
        items = chest["items"]
        
        # Format items to SNBT
        items_snbt = to_snbt(items)
        cmd = f"data modify block {x} {y} {z} Items set value {items_snbt}"
        print(f"Restoring chest at ({x}, {y}, {z})...")
        send_command(cmd)
        
        # Clean dropped items
        cleanup_cmd = f"execute positioned {x} {y} {z} run kill @e[type=item,distance=..10]"
        send_command(cleanup_cmd)
        time.sleep(0.5)
        
    print("Undo completed successfully.")

def clear_chests():
    if not os.path.exists(ALL_CHESTS_FILE):
        print(f"Error: {ALL_CHESTS_FILE} not found.")
        sys.exit(1)
        
    with open(ALL_CHESTS_FILE, "r") as f:
        all_chests = json.load(f)
        
    # Get wilderness chests with items
    wild_chests = []
    for c in all_chests:
        regions = c.get("regions", [])
        items_count = c.get("items_count", 0)
        if (not regions or len(regions) == 0) and items_count > 0:
            wild_chests.append(c)
            
    if not wild_chests:
        print("No populated wilderness chests found to clear.")
        return
        
    print(f"Found {len(wild_chests)} populated wilderness chest(s). Creating backup...")
    
    # Save backup
    with open(BACKUP_FILE, "w") as f:
        json.dump(wild_chests, f, indent=4)
    print(f"Backup saved to: {BACKUP_FILE}")
    
    # Clear each chest
    for c in wild_chests:
        x, y, z = c["x"], c["y"], c["z"]
        print(f"Clearing chest at ({x}, {y}, {z}) containing {c['items_count']} items...")
        
        # Clear items from chest
        clear_cmd = f"data remove block {x} {y} {z} Items"
        send_command(clear_cmd)
        
        # Kill any dropped item entities nearby
        cleanup_cmd = f"execute positioned {x} {y} {z} run kill @e[type=item,distance=..10]"
        send_command(cleanup_cmd)
        time.sleep(0.5)
        
    # Also update the local database file (set items to empty list and items_count to 0)
    for c in all_chests:
        regions = c.get("regions", [])
        if (not regions or len(regions) == 0):
            c["items"] = []
            c["items_count"] = 0
            
    with open(ALL_CHESTS_FILE, "w") as f:
        json.dump(all_chests, f, indent=4)
        
    print("All wilderness chests cleared successfully and local database updated.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--undo":
        undo()
    else:
        clear_chests()
