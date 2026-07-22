#!/usr/bin/env python3
"""
Expanded Floor Construction Script with Strict Rollback/Undo Support
-------------------------------------------------------------------
Applies or reverts floor block placement for region expansions.
"""

import os
import sys
import json
import subprocess
import argparse

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

HISTORY_FILE = "WorldGuard/backups/floor_history.json"

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
    return res.stdout

def main():
    parser = argparse.ArgumentParser(description="Manage expanded plot floor blocks with undo support")
    parser.add_argument("--undo", action="store_true", help="Undo the floor block placement")
    parser.add_argument("--material", default="minecraft:light_gray_concrete", help="Block type for floor")
    args = parser.parse_args()

    if args.undo:
        if not os.path.exists(HISTORY_FILE):
            print("❌ No floor history found to undo.")
            sys.exit(1)
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
        record = history.get("hanansaleh_expansion")
        if not record:
            print("❌ No record found for hanansaleh_expansion.")
            sys.exit(1)
        undo_cmd = record["undo_cmd"]
        print(f"🔄 Executing undo: {undo_cmd}")
        out = send_exaroton_command(undo_cmd)
        print("Response:", out)
        del history["hanansaleh_expansion"]
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
        print("✨ Successfully undone floor placement.")
    else:
        fill_cmd = f"execute in minecraft:overworld run fill 1292 78 -238 1299 78 -231 {args.material}"
        print(f"🔨 Placing floor: {fill_cmd}")
        out = send_exaroton_command(fill_cmd)
        print("Response:", out)
        
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        history = {}
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    history = json.load(f)
            except Exception:
                pass
        history["hanansaleh_expansion"] = {
            "action": "floor_fill",
            "material": args.material,
            "min_x": 1292,
            "max_x": 1299,
            "y": 78,
            "min_z": -238,
            "max_z": -231,
            "undo_cmd": "execute in minecraft:overworld run fill 1292 78 -238 1299 78 -231 minecraft:air"
        }
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
        print("📝 History updated.")

if __name__ == "__main__":
    main()
