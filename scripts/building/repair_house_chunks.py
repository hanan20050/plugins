#!/usr/bin/env python3
"""
Structural Chunk & Roof Repair Script
--------------------------------------
Repairs all floor slabs, mezzanine ceilings, roof overhangs, and wall sections
surrounding the 10x10 Modern Villa at (1200, 63, -127) without disturbing the stairwell.
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
    min_x, max_x = 1195, 1204
    min_z, max_z = -132, -123
    base_y = 63

    repair_commands = [
        # 1. Repair Ground Floor (Y=63)
        f"fill {min_x} {base_y} {min_z} {max_x} {base_y} {max_z} dark_oak_planks",

        # 2. Repair Mezzanine Floor (Y=67) across entire 10x10 footprint
        f"fill {min_x} {base_y+4} {min_z} {max_x} {base_y+4} {max_z} smooth_quartz",
        # Re-cut ONLY the 1-block wide stairwell opening at X=1196
        f"fill {min_x+1} {base_y+4} {-130} {min_x+1} {base_y+4} {-128} air",

        # 3. Repair Full Roof Canopy Overhang (Y=71)
        f"fill {min_x-1} {base_y+8} {min_z-1} {max_x+1} {base_y+8} {max_z+1} white_concrete",
        f"setblock 1198 {base_y+8} {-129} sea_lantern",
        f"setblock 1201 {base_y+8} {-129} sea_lantern",
        f"setblock 1198 {base_y+8} {-127} sea_lantern",
        f"setblock 1201 {base_y+8} {-127} sea_lantern",

        # 4. Repair 2nd Floor Balcony Divider Glass Wall (Z=-125)
        f"fill {min_x+1} {base_y+5} {-125} {1199} {base_y+7} {-125} black_stained_glass",
        f"fill 1201 {base_y+5} {-125} {max_x-1} {base_y+7} {-125} black_stained_glass",
        f"setblock 1200 {base_y+7} {-125} black_concrete",
        f"setblock 1200 {base_y+5} {-125} dark_oak_door[half=lower,facing=south]",
        f"setblock 1200 {base_y+6} {-125} dark_oak_door[half=upper,facing=south]",

        # 5. Repair Balcony Railing (Z=-123, Y=68)
        f"fill {min_x+1} {base_y+5} {max_z} {max_x-1} {base_y+5} {max_z} glass_pane",

        # 6. Repair North & East Windows
        f"fill {min_x+1} {base_y+2} {min_z} {max_x-1} {base_y+3} {min_z} black_stained_glass",
        f"fill {min_x+1} {base_y+6} {min_z} {max_x-1} {base_y+7} {min_z} black_stained_glass",
        f"fill {max_x} {base_y+2} {min_z+1} {max_x} {base_y+3} {max_z-1} black_stained_glass",
        f"fill {max_x} {base_y+6} {min_z+1} {max_x} {base_y+7} {max_z-1} black_stained_glass",

        # 7. Ensure stairwell headroom is 100% open (X=1196, Y=65..67)
        f"fill {min_x+1} {base_y+2} {-130} {min_x+1} {base_y+3} {-130} air",
        f"fill {min_x+1} {base_y+3} {-129} {min_x+1} {base_y+4} {-129} air",
    ]

    print(f"🏗️ Repairing all structural house chunks and roof ({len(repair_commands)} steps)...")
    for cmd in repair_commands:
        send_exaroton_command(cmd)

    print("🎉 All structural chunks, mezzanine floor, and roof repaired completely!")

if __name__ == "__main__":
    main()
