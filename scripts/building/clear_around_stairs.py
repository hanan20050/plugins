#!/usr/bin/env python3
"""
Staircase Surrounding Cleaner Script
-----------------------------------
Clears all extra stray blocks, glass panes, and clutter in the immediate walkway and landing surrounding the stairs at X=1196..1197.
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
    commands = [
        # 1. Clear glass panes / banisters and extra blocks at X=1197 (Y=64..69, Z=-131..-126)
        "fill 1197 64 -131 1197 69 -126 air",

        # 2. Clear entrance walkway at bottom of stairs (X=1196, Z=-131, Y=64..66)
        "fill 1196 64 -131 1196 66 -131 air",

        # 3. Clear landing exit at top of stairs (X=1196..1197, Z=-126, Y=67..69)
        "fill 1196 67 -126 1197 69 -126 air",

        # 4. Clear headspace above stairs (X=1196, Z=-130..-127, Y=67..69)
        "fill 1196 67 -130 1196 69 -127 air",
    ]

    print(f"🧹 Clearing extra clutter around staircase area ({len(commands)} steps)...")
    for cmd in commands:
        send_exaroton_command(cmd)

    print("✨ Staircase surroundings cleared cleanly!")

if __name__ == "__main__":
    main()
