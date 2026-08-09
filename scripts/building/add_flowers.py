#!/usr/bin/env python3
"""
Surgically add beautiful jungle flowers and a spore blossom to the mini jungle biome area.
Adheres to the Additive & Surgical Modification Rule (does not clear any blocks).
"""

import os
import sys
import json
import subprocess

ENV_FILE = ".env"
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
    try:
        data = json.loads(res.stdout)
        return data.get("success", False)
    except Exception:
        return False

def main():
    print("=== Surgically Adding Flowers to Mini Jungle ===")
    
    cmds = [
        # Place beautiful flowers at Y=79 in empty coordinates
        "setblock 1293 79 -238 minecraft:blue_orchid",
        "setblock 1296 79 -238 minecraft:lily_of_the_valley",
        "setblock 1298 79 -238 minecraft:allium",
        "setblock 1294 79 -234 minecraft:poppy",
        "setblock 1296 79 -234 minecraft:dandelion",
        "setblock 1297 79 -232 minecraft:blue_orchid",
        "setblock 1299 79 -232 minecraft:pink_petals[flower_amount=4]",
        
        # Hang a spore blossom under tree leaves for lush green particle effects
        "setblock 1295 81 -235 minecraft:spore_blossom"
    ]
    
    success_count = 0
    for cmd in cmds:
        if send_exaroton_command(cmd):
            success_count += 1
            print(f"✅ Executed: {cmd}")
        else:
            print(f"❌ Failed: {cmd}")
            
    print(f"Done! {success_count}/{len(cmds)} commands executed successfully.")

if __name__ == "__main__":
    main()
