#!/usr/bin/env python3
"""
Digital Economy ($) ATM Deposit & Withdraw System
-------------------------------------------------
Strict Fixed Rates:
- 1 Emerald (minecraft:emerald)           = $1
- 1 Emerald Block (minecraft:emerald_block)  = $9
- 1 Netherite Ingot (minecraft:netherite_ingot) = $64
- 1 Netherite Block (minecraft:netherite_block) = $576

Commands:
- python3 deposit_withdraw_atm.py deposit <player> <item_type> <amount>
- python3 deposit_withdraw_atm.py withdraw <player> <item_type> <amount>
- python3 deposit_withdraw_atm.py balance <player>
"""

import sys
import os
import json
import subprocess

# Strict Exchange Rates ($ per unit)
EXCHANGE_RATES = {
    "emerald": 1,
    "minecraft:emerald": 1,
    "emerald_block": 9,
    "minecraft:emerald_block": 9,
    "netherite_ingot": 64,
    "minecraft:netherite_ingot": 64,
    "netherite_block": 576,
    "minecraft:netherite_block": 576
}

ITEM_NAMES = {
    "emerald": "minecraft:emerald",
    "minecraft:emerald": "minecraft:emerald",
    "emerald_block": "minecraft:emerald_block",
    "minecraft:emerald_block": "minecraft:emerald_block",
    "netherite_ingot": "minecraft:netherite_ingot",
    "minecraft:netherite_ingot": "minecraft:netherite_ingot",
    "netherite_block": "minecraft:netherite_block",
    "minecraft:netherite_block": "minecraft:netherite_block"
}

def load_env():
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    config = {}
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()
    token = os.environ.get("EXAROTON_TOKEN") or config.get("EXAROTON_TOKEN")
    server_id = os.environ.get("EXAROTON_SERVER_ID") or config.get("EXAROTON_SERVER_ID")
    return token, server_id

def run_cmd(command):
    token, server_id = load_env()
    url = f"https://api.exaroton.com/v1/servers/{server_id}/command/"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"command": command})
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    return res.stdout

def deposit(player, item_type, amount):
    item_key = item_type.lower()
    if item_key not in EXCHANGE_RATES:
        print(f"Error: Invalid item '{item_type}'. Allowed: emerald, emerald_block, netherite_ingot, netherite_block")
        return

    rate = EXCHANGE_RATES[item_key]
    mc_item = ITEM_NAMES[item_key]
    total_dollar = rate * amount

    print(f"Depositing {amount}x {mc_item} for player {player} (${total_dollar} total)...")
    # 1. Clear physical items from player inventory
    clear_cmd = f"clear {player} {mc_item} {amount}"
    res_clear = run_cmd(clear_cmd)
    print(f"Clear Result: {res_clear.strip()}")

    # 2. Add digital dollars via eco command
    eco_cmd = f"eco give {player} {total_dollar}"
    res_eco = run_cmd(eco_cmd)
    print(f"Eco Result: {res_eco.strip()}")

    # 3. Notify player
    msg_cmd = f"msg {player} §a[ATM] Deposited {amount}x {mc_item} into your account. Added ${total_dollar}!"
    run_cmd(msg_cmd)

def withdraw(player, item_type, amount):
    item_key = item_type.lower()
    if item_key not in EXCHANGE_RATES:
        print(f"Error: Invalid item '{item_type}'. Allowed: emerald, emerald_block, netherite_ingot, netherite_block")
        return

    rate = EXCHANGE_RATES[item_key]
    mc_item = ITEM_NAMES[item_key]
    total_dollar = rate * amount

    print(f"Withdrawing {amount}x {mc_item} for player {player} (${total_dollar} total)...")
    # 1. Deduct digital dollars via eco command
    eco_cmd = f"eco take {player} {total_dollar}"
    res_eco = run_cmd(eco_cmd)
    print(f"Eco Result: {res_eco.strip()}")

    # 2. Give physical items to player inventory
    give_cmd = f"give {player} {mc_item} {amount}"
    res_give = run_cmd(give_cmd)
    print(f"Give Result: {res_give.strip()}")

    # 3. Notify player
    msg_cmd = f"msg {player} §a[ATM] Withdrew {amount}x {mc_item} from your account (-${total_dollar})."
    run_cmd(msg_cmd)

def balance(player):
    cmd = f"eco take {player} 0"
    res = run_cmd(cmd)
    print(f"Balance check response for {player}: {res.strip()}")

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python3 deposit_withdraw_atm.py deposit <player> <item_type> <amount>")
        print("  python3 deposit_withdraw_atm.py withdraw <player> <item_type> <amount>")
        print("  python3 deposit_withdraw_atm.py balance <player>")
        sys.exit(1)

    action = sys.argv[1].lower()
    player = sys.argv[2]

    if action == "deposit":
        if len(sys.argv) < 5:
            print("Error: Specify item_type and amount")
            sys.exit(1)
        item_type = sys.argv[3]
        amount = int(sys.argv[4])
        deposit(player, item_type, amount)
    elif action == "withdraw":
        if len(sys.argv) < 5:
            print("Error: Specify item_type and amount")
            sys.argv[4]
        item_type = sys.argv[3]
        amount = int(sys.argv[4])
        withdraw(player, item_type, amount)
    elif action == "balance":
        balance(player)
    else:
        print(f"Unknown action '{action}'")

if __name__ == "__main__":
    main()
