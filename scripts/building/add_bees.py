#!/usr/bin/env python3
"""
Add Bee Nests and summon Bees in the mini jungle biome area of the villager region.
Does not remove any existing blocks.
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
    print("=== Adding Bee Nests and Summoning Bees ===")
    
    cmds = [
        # 1. Place Bee Nests attached to the trees
        "setblock 1295 80 -237 minecraft:bee_nest[facing=north]",
        "setblock 1298 80 -233 minecraft:bee_nest[facing=south]",
        
        # 2. Summon Bees near the nests
        "summon minecraft:bee 1295 81 -237",
        "summon minecraft:bee 1295 81 -237",
        "summon minecraft:bee 1298 81 -233",
        "summon minecraft:bee 1298 81 -233"
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
