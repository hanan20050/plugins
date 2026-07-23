#!/usr/bin/env python3
"""
rayan_scam_payback_system.py
-----------------------------
Automated 75% Payback & Chest Seizure Tracker for Rayan Saleh (NightmareDady).

- Scam Amount: 5000 Emeralds
- Target Revoke/Payback (75%): 3750 Emeralds
- Fast Chest Scanning: Queries known chest locations in Rayan's region instantly.
- Revokes/clears items from chests and player inventory, converts item value to Emerald equivalent, and credits towards 3750 Emerald goal.
- Scans Shopkeepers trades for Rayan's new selling income/earnings and revokes/deducts income.
- Broadcasts server-wide tellraw notifications to EVERYONE on the server.
- State file: `rayan_scam_payback_state.json`
"""

import os
import sys
import json
import re
import time
import subprocess
import sqlite3
from datetime import datetime

# Fallback credentials setup
EXAROTON_TOKEN = os.getenv("EXAROTON_TOKEN", "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ")
EXAROTON_SERVER_ID = os.getenv("EXAROTON_SERVER_ID", "cEuS61sZvNEFS3aB")
os.environ["EXAROTON_TOKEN"] = EXAROTON_TOKEN
os.environ["EXAROTON_SERVER_ID"] = EXAROTON_SERVER_ID

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "rayan_scam_payback_state.json")

TOTAL_SCAM = 5000
TARGET_PAYBACK = int(TOTAL_SCAM * 0.75) # 3750 Emeralds

# Price conversions in Emeralds
ITEM_EMERALD_VALUES = {
    "minecraft:emerald": 1,
    "minecraft:emerald_block": 9,
    "minecraft:netherite_ingot": 64,
    "minecraft:netherite_block": 576,
    "minecraft:diamond": 5,
    "minecraft:diamond_block": 45,
    "minecraft:gold_ingot": 1,
    "minecraft:gold_block": 9,
    "minecraft:iron_ingot": 0.5,
    "minecraft:iron_block": 4.5,
    "minecraft:enchanted_book": 10,
}

# Known chest locations in Rayan's region (y=80)
KNOWN_CHEST_COORDS = [
    (1310, 80, -232), (1311, 80, -232),
    (1304, 80, -238), (1305, 80, -238),
    (1313, 80, -233), (1314, 80, -233),
    (1315, 80, -233), (1316, 80, -233),
    (1314, 80, -238), (1315, 80, -238),
    (1316, 80, -238), (1313, 80, -238)
]

# Rayan Identifiers
RAYAN_USERNAMES = ["NightmareDady", ".WiryCircle3938"]

def execute_exaroton_cmd(cmd):
    """Executes a console command on Exaroton server via API."""
    try:
        url = f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}/command/"
        body = json.dumps({"command": cmd})
        res = subprocess.run(
            [
                "curl", "-s",
                "--resolve", "api.exaroton.com:443:104.26.12.211",
                "-X", "POST", url,
                "-H", f"Authorization: Bearer {EXAROTON_TOKEN}",
                "-H", "Content-Type: application/json",
                "-d", body
            ],
            capture_output=True, text=True, timeout=10
        )
        return res.stdout
    except Exception as e:
        print(f"Error executing console command '{cmd}': {e}")
        return ""

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "target_emeralds": TARGET_PAYBACK,
        "recovered_emeralds": 0,
        "is_completed": False,
        "cleared_chests": [],
        "last_trade_id": 0,
        "history": []
    }

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def notify_everyone(msg):
    """Broadcasts scam recovery notifications to EVERYONE on the server via tellraw."""
    msg_json = json.dumps([
        {"text": "[SCAM RECOVERY SYSTEM] ", "color": "red", "bold": True},
        {"text": msg, "color": "yellow"}
    ])
    cmd = f"tellraw @a {msg_json}"
    execute_exaroton_cmd(cmd)

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
            start = i
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
        while i < len(s) and s[i] not in " \t\r\n{}[],:\"":
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
            return v
    return parse_value()

def scan_and_clear_chests(state):
    """Scans Rayan's chests and clears items, converting value to Emeralds."""
    if state["is_completed"]:
        return

    # First scan known chest coordinates
    for x, y, z in KNOWN_CHEST_COORDS:
        out = execute_exaroton_cmd(f"data get block {x} {y} {z}")
        if "has the following block data:" in out and "Items:" in out:
            match = re.search(r"has the following block data:\s*(\{.*\})", out, re.DOTALL)
            if match:
                nbt_raw = match.group(1)
                nbt_data = parse_snbt(nbt_raw)
                if nbt_data and isinstance(nbt_data, dict) and "Items" in nbt_data:
                    items = nbt_data["Items"]
                    chest_emeralds = 0
                    item_count = 0
                    if isinstance(items, list) and len(items) > 0:
                        for item in items:
                            if isinstance(item, dict):
                                id_str = item.get("id", "")
                                count = int(re.sub(r"[^\d]", "", str(item.get("Count", 1))) or 1)
                                val_per_unit = ITEM_EMERALD_VALUES.get(id_str, 0.5)
                                chest_emeralds += (count * val_per_unit)
                                item_count += count
                        
                        # Replace chest with fresh empty chest
                        execute_exaroton_cmd(f"setblock {x} {y} {z} minecraft:chest replace")
                        
                        needed = state["target_emeralds"] - state["recovered_emeralds"]
                        credited = min(chest_emeralds, needed)
                        state["recovered_emeralds"] += credited
                        rem = max(0, state["target_emeralds"] - state["recovered_emeralds"])
                        
                        log_entry = f"Seized chest at ({x},{y},{z}): {item_count} items worth ~{chest_emeralds:.1f} emeralds. Credited: {credited:.1f} E."
                        state["history"].append(log_entry)
                        print(log_entry)
                        
                        notify_everyone(f"Seized items from Rayan Saleh (NightmareDady) chest at {x},{y},{z} (~{credited:.1f} Emeralds value). Remaining scam debt: {rem:.1f} Emeralds.")
                        
                        if state["recovered_emeralds"] >= state["target_emeralds"]:
                            state["is_completed"] = True
                            notify_everyone("Rayan Saleh's scam debt of 3750 Emeralds (75%) has been FULLY RECOVERED by the server!")
                            save_state(state)
                            return

    # Clear all chest items in volume via bulk fill command
    execute_exaroton_cmd("execute in minecraft:overworld run fill 1302 79 -240 1319 86 -230 minecraft:chest replace minecraft:chest")

    # Clear inventory of online Rayan if present
    for u in RAYAN_USERNAMES:
        execute_exaroton_cmd(f"clear {u} minecraft:emerald")
        execute_exaroton_cmd(f"clear {u} minecraft:emerald_block")
        execute_exaroton_cmd(f"clear {u} minecraft:netherite_ingot")
        execute_exaroton_cmd(f"clear {u} minecraft:netherite_block")

def check_new_income(state):
    """Tracks Rayan's trades log to capture and revoke newly earned income."""
    if state["is_completed"]:
        return

    db_path = os.path.join(BASE_DIR, "Shopkeepers", "trade-logs", "trades.db")
    if not os.path.exists(db_path):
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        last_id = state.get("last_trade_id", 0)
        cursor.execute("SELECT rowid, player_name, result_item_type, result_item_amount FROM trade WHERE rowid > ? ORDER BY rowid ASC", (last_id,))
        rows = cursor.fetchall()
        
        for row in rows:
            trade_id, player_name, result_item, result_amount = row
            state["last_trade_id"] = trade_id
            
            if any(p.lower() in player_name.lower() for p in RAYAN_USERNAMES):
                clean_item = f"minecraft:{result_item.lower()}"
                val = ITEM_EMERALD_VALUES.get(clean_item, 1) * result_amount
                needed = state["target_emeralds"] - state["recovered_emeralds"]
                credited = min(val, needed)
                state["recovered_emeralds"] += credited
                rem = max(0, state["target_emeralds"] - state["recovered_emeralds"])
                
                # Revoke earnings from player's inventory
                execute_exaroton_cmd(f"clear {player_name} {clean_item} {result_amount}")
                
                log_entry = f"Revoked earnings from trade #{trade_id} ({result_amount}x {clean_item}): Credited {credited:.1f} E."
                state["history"].append(log_entry)
                print(log_entry)
                
                notify_everyone(f"Revoked income ({result_amount}x {result_item}) from Rayan Saleh (NightmareDady) for scam payback (~{credited:.1f} E). Remaining debt: {rem:.1f} Emeralds.")
                
                if state["recovered_emeralds"] >= state["target_emeralds"]:
                    state["is_completed"] = True
                    notify_everyone("Rayan Saleh's scam debt of 3750 Emeralds (75%) has been FULLY RECOVERED by the server!")
                    break
        conn.close()
    except Exception as e:
        print(f"Error checking trade income: {e}")

def run_scam_payback_cycle():
    state = load_state()
    if state["is_completed"]:
        return

    # 1. Scan and clear Rayan's chests
    scan_and_clear_chests(state)
    
    # 2. Check trade income
    check_new_income(state)
    
    save_state(state)

if __name__ == "__main__":
    print("Running Rayan Scam Payback Cycle...")
    run_scam_payback_cycle()
