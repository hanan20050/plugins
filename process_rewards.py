#!/usr/bin/env python3
import os
import json
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REWARDS_FILE = os.path.join(BASE_DIR, "pending_rewards.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")

CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or "cEuS61sZvNEFS3aB"

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
    return res.stdout

def get_online_players():
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "GET", url,
        "-H", f"Authorization: Bearer {TOKEN}"
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        return data.get("data", {}).get("players", {}).get("list", [])
    except Exception as e:
        print(f"Error fetching online players: {e}")
        return []

def main():
    if not os.path.exists(REWARDS_FILE):
        print("No pending_rewards.json file found.")
        return

    with open(REWARDS_FILE, "r") as f:
        rewards = json.load(f)

    if not rewards:
        print("No pending rewards to process.")
        return

    # 1. Reset balances to zero first (one-time action per player)
    for player, data in list(rewards.items()):
        if not data.get("balance_reset_done", False):
            print(f"Resetting balance of {player} to 0...")
            send_exaroton_command(f"eco set {player} 0")
            rewards[player]["balance_reset_done"] = True
            with open(REWARDS_FILE, "w") as f:
                json.dump(rewards, f, indent=2)

    # 2. Check who is online and process their rewards
    online_players = get_online_players()
    print("Online players:", online_players)

    for player, data in list(rewards.items()):
        # Exclude players who have already received all their items
        blocks = data.get("blocks", 0)
        emeralds = data.get("emeralds", 0)
        if blocks == 0 and emeralds == 0:
            continue

        # Check if player is online (ignoring case or prefix for Geyser players)
        is_online = False
        match_name = player
        for op in online_players:
            if op.lower() == player.lower() or op.lower() == player.lstrip(".").lower():
                is_online = True
                match_name = op
                break

        if is_online:
            print(f"Player {player} is online! Issuing rewards...")
            
            # Give emerald blocks in stacks of 64
            rem_blocks = blocks
            while rem_blocks > 0:
                give_amount = min(rem_blocks, 64)
                send_exaroton_command(f"give {match_name} minecraft:emerald_block {give_amount}")
                rem_blocks -= give_amount
            
            # Give remaining emeralds
            if emeralds > 0:
                send_exaroton_command(f"give {match_name} minecraft:emerald {emeralds}")

            # Notify the player privately
            send_exaroton_command(f"msg {match_name} You have been given your emeralds from your converted balance!")

            # Clear rewards in dict
            rewards[player]["blocks"] = 0
            rewards[player]["emeralds"] = 0

            # Save updated file
            with open(REWARDS_FILE, "w") as f:
                json.dump(rewards, f, indent=2)
            print(f"Successfully processed and cleared rewards for {player}.")

if __name__ == "__main__":
    main()
