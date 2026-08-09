#!/usr/bin/env python3
"""
Timed Floor Outline Changer script for Rayan's Old Plot (`nightmaredady`)
Fills floor outline with specified colored concrete (default: magenta_concrete) for 30 seconds,
broadcasting updates every 10 seconds via tellraw chat updates (per project rules),
and then reverts the outline back to stone_bricks.
"""

import os
import sys
import json
import time
import subprocess

HARDCODED_TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
HARDCODED_SERVER_ID = "cEuS61sZvNEFS3aB"

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or HARDCODED_TOKEN
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or HARDCODED_SERVER_ID

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
        if data.get("success"):
            print(f"✅ Console Executed: {cmd}")
            return True
        else:
            print(f"❌ Command Error: {data.get('error')} | Output: {res.stdout}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def broadcast_tellraw(msg):
    tellraw_cmd = f'tellraw @a {json.dumps([{"text": "[Floor Effect] ", "color": "light_purple", "bold": True}, {"text": msg, "color": "yellow"}])}'
    send_exaroton_command(tellraw_cmd)

def set_floor_outline(min_x, min_z, max_x, max_z, floor_y, mat):
    cmds = [
        f"fill {min_x} {floor_y} {min_z} {max_x} {floor_y} {min_z} {mat}",
        f"fill {min_x} {floor_y} {max_z} {max_x} {floor_y} {max_z} {mat}",
        f"fill {min_x} {floor_y} {min_z} {min_x} {floor_y} {max_z} {mat}",
        f"fill {max_x} {floor_y} {min_z} {max_x} {floor_y} {max_z} {mat}"
    ]
    for c in cmds:
        send_exaroton_command(c)

def main():
    # Bounds for Rayan's old plot (`nightmaredady`)
    # min: {x: 1302, y: 79, z: -240}
    # max: {x: 1311, y: 86, z: -230}
    min_x, max_x = 1302, 1311
    min_z, max_z = -240, -230
    floor_y = 79

    colored_mat = sys.argv[1] if len(sys.argv) > 1 else "minecraft:magenta_concrete"
    if not colored_mat.startswith("minecraft:"):
        colored_mat = f"minecraft:{colored_mat}"
    
    revert_mat = "minecraft:stone_bricks"
    duration = 30 # seconds

    print(f"🎨 Filling Rayan's old plot (`nightmaredady`) floor outline with '{colored_mat}' for {duration} seconds...")
    set_floor_outline(min_x, min_z, max_x, max_z, floor_y, colored_mat)
    broadcast_tellraw(f"Rayan's plot floor outline set to colored cement ({colored_mat.split(':')[-1]}) for {duration} seconds!")

    start_time = time.time()
    for elapsed in [10, 20]:
        time_to_sleep = start_time + elapsed - time.time()
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)
        remaining = duration - elapsed
        broadcast_tellraw(f"Floor outline effect: {elapsed}s passed, {remaining}s remaining...")

    time_to_sleep = start_time + duration - time.time()
    if time_to_sleep > 0:
        time.sleep(time_to_sleep)

    print(f"🔄 Reverting Rayan's old plot floor outline back to '{revert_mat}'...")
    set_floor_outline(min_x, min_z, max_x, max_z, floor_y, revert_mat)
    broadcast_tellraw(f"Floor outline effect ended. Restored to stone bricks!")
    print("✨ Floor outline temporary effect complete!")

if __name__ == "__main__":
    main()
