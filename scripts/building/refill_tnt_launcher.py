#!/usr/bin/env python3
"""
Refills all dispensers of the TNT launcher at X=1196, Y=63, Z=-128 with full stacks of TNT.
"""

import os
import json
import subprocess

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
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
        if data.get("success"):
            print(f"✅ Executed: {cmd}")
        else:
            print(f"❌ Error: {data.get('error')}")
    except Exception:
        print(f"Response: {res.stdout}")

def main():
    cx, cy, cz = 1196, 63, -128
    dispensers = [
        (cx-1, cy+1, cz),   # Propellant left 1
        (cx-1, cy+1, cz-1), # Propellant left 2
        (cx-1, cy+1, cz-2), # Propellant left 3
        (cx+1, cy+1, cz),   # Propellant right 1
        (cx+1, cy+1, cz-1), # Propellant right 2
        (cx+1, cy+1, cz-2), # Propellant right 3
        (cx, cy+2, cz-3)    # Projectile
    ]

    print("Refilling TNT dispensers...")
    for dx, dy, dz in dispensers:
        for slot in range(9):
            send_exaroton_command(f"item replace block {dx} {dy} {dz} container.{slot} with tnt 64")
    print("Done!")

if __name__ == "__main__":
    main()
