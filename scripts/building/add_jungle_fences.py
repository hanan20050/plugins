#!/usr/bin/env python3
"""
Adds jungle fences *inside* the mini jungle region bounds (X: 1293 to 1300, Z: -239 to -231, Y: 78).
Fences are placed at Y=79 on the North (Z=-239), West (X=1293), and East (X=1300) internal borders.
No fences are placed on the South side (Z=-231) facing the villager house.
Supports --undo.
"""

import os
import sys
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
    if "--undo" in sys.argv:
        print("Undoing internal fences...")
        # Clear West border fences
        send_exaroton_command("fill 1293 79 -239 1293 79 -231 air replace jungle_fence")
        # Clear East border fences
        send_exaroton_command("fill 1300 79 -239 1300 79 -231 air replace jungle_fence")
        # Clear North border fences
        send_exaroton_command("fill 1294 79 -239 1299 79 -239 air replace jungle_fence")
        print("Done undoing internal fences!")
    else:
        print("Placing internal jungle fences...")
        # West fence line (X=1293, Z=-239 to -231)
        send_exaroton_command("fill 1293 79 -239 1293 79 -231 jungle_fence")
        # East fence line (X=1300, Z=-239 to -231)
        send_exaroton_command("fill 1300 79 -239 1300 79 -231 jungle_fence")
        # North fence line (Z=-239, X=1294 to 1299)
        send_exaroton_command("fill 1294 79 -239 1299 79 -239 jungle_fence")
        print("Done placing internal fences!")

if __name__ == "__main__":
    main()
