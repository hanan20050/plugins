#!/usr/bin/env python3
"""
Temporary Clear 'A' Shape Script
- Temporarily replaces the Yellow 'A' shape blocks on Y=63 with air.
- Clears dropped items.
- Waits for 10 seconds.
- Restores the Yellow 'A' shape blocks (Yellow Concrete).
- Clears dropped items again.
"""

import os
import sys
import json
import time
import subprocess

PLUGINS_DIR = "/Users/hanansaleh/Downloads/plugins"

# Load environment variables from .env
ENV_FILE = os.path.join(PLUGINS_DIR, ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()

HARDCODED_TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
HARDCODED_SERVER_ID = "cEuS61sZvNEFS3aB"

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or HARDCODED_TOKEN
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or HARDCODED_SERVER_ID

FLOOR_Y = 63

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

def set_a_material(material):
    commands = [
        f"fill 1058 {FLOOR_Y} -157 1058 {FLOOR_Y} -147 {material}",
        f"fill 1066 {FLOOR_Y} -157 1066 {FLOOR_Y} -147 {material}",
        f"fill 1058 {FLOOR_Y} -157 1066 {FLOOR_Y} -157 {material}",
        f"fill 1058 {FLOOR_Y} -152 1066 {FLOOR_Y} -152 {material}"
    ]
    for cmd in commands:
        send_exaroton_command(cmd)

    # Immediately clear dropped item loot
    clear_loot_cmd = f"kill @e[type=item,x=1062,y={FLOOR_Y},z=-152,distance=..20]"
    send_exaroton_command(clear_loot_cmd)

def main():
    print("Replacing Yellow 'A' with air...")
    set_a_material("minecraft:air")
    
    print("Waiting 10 seconds...")
    time.sleep(10)
    
    print("Restoring Yellow Concrete 'A'...")
    set_a_material("minecraft:yellow_concrete")
    print("Done!")

if __name__ == "__main__":
    main()
