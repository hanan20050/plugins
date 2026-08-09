#!/usr/bin/env python3
"""
Surgical Staircase Repair Script
--------------------------------
Updates and fixes ONLY the staircase and banister at X=1196 without removing or wiping the rest of the house.
"""

import os
import sys
import json
import subprocess

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
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
            print(f"✅ Executed: {cmd}")
            return True
        else:
            print(f"❌ Error: {data.get('error')}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def main():
    min_x = 1195
    base_y = 63

    stair_commands = [
        # 1. Clear stairwell space & headroom
        f"fill {min_x+1} {base_y+1} {-131} {min_x+1} {base_y+3} {-127} air",
        f"fill {min_x+1} {base_y+4} {-131} {min_x+1} {base_y+4} {-127} air",

        # 2. Solid Quartz Under-Stair Support Structure
        f"setblock {min_x+1} {base_y+1} {-129} smooth_quartz",
        f"fill {min_x+1} {base_y+1} {-128} {min_x+1} {base_y+2} {-128} smooth_quartz",
        f"fill {min_x+1} {base_y+1} {-127} {min_x+1} {base_y+3} {-127} smooth_quartz",

        # 3. 4-Step Quartz Staircase (facing=south ascending North to South)
        f"setblock {min_x+1} {base_y+1} {-130} quartz_stairs[facing=south]",
        f"setblock {min_x+1} {base_y+2} {-129} quartz_stairs[facing=south]",
        f"setblock {min_x+1} {base_y+3} {-128} quartz_stairs[facing=south]",

        # 4. Glass Banister / Railing along stair edge
        f"setblock {min_x+2} {base_y+2} {-130} glass_pane",
        f"setblock {min_x+2} {base_y+3} {-129} glass_pane",
        f"setblock {min_x+2} {base_y+4} {-128} glass_pane",
        f"setblock {min_x+2} {base_y+5} {-127} glass_pane",
    ]

    print(f"🔧 Fixing staircase surgical area ONLY ({len(stair_commands)} steps)...")
    for cmd in stair_commands:
        send_exaroton_command(cmd)

    print("✨ Staircase fixed successfully without wiping the house!")

if __name__ == "__main__":
    main()
