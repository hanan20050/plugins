#!/usr/bin/env python3
import os
import sys
import json
import subprocess

# Load environment variables from root .env
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE = os.path.join(ROOT_DIR, ".env")
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
    # manan2 bounds
    min_x, max_x = 1088, 1137
    min_z, max_z = -127, -78
    floor_y = 63

    if "--undo" in sys.argv:
        print("🔄 Reverting manan2 floor outline to grass_block...")
        set_floor_outline(min_x, min_z, max_x, max_z, floor_y, "minecraft:grass_block")
        # Clear dropped item loot in the affected area
        send_exaroton_command(f"minecraft:kill @e[type=item,x=1112,y=63,z=-102,distance=..40]")
        print("✔ Revert complete & entities cleared.")
    else:
        print("🎨 Drawing manan2 floor outline with blue_concrete...")
        set_floor_outline(min_x, min_z, max_x, max_z, floor_y, "minecraft:blue_concrete")
        print("✔ Outline complete.")

if __name__ == "__main__":
    main()
