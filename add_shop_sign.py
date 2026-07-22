#!/usr/bin/env python3
"""
WorldGuard Shop Sign Generator (with Undo Support)
--------------------------------------------------
Places an oak wall sign above the entrance/gate of the 'shop' region
displaying "=== SHOP ===" with full backup and --undo support.

Usage:
  python3 add_shop_sign.py [--text "SHOP"] [--dry-run]
  python3 add_shop_sign.py --undo [--dry-run]
"""

import os
import sys
import json
import re
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

HISTORY_FILE = "WorldGuard/backups/shop_sign_history.json"

def send_exaroton_command(cmd, dry_run=False):
    if dry_run:
        print(f"[DRY-RUN] Console command: {cmd}")
        return True
    
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
            print(f"✅ Executed console command: {cmd}")
            return True
        else:
            print(f"❌ Exaroton Command Error: {data.get('error')}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def save_sign_history(coords, block_type):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = {
        "coords": coords,
        "block_type": block_type
    }
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)
    print(f"📝 Sign placement history saved to '{HISTORY_FILE}'.")

def load_sign_history():
    if not os.path.exists(HISTORY_FILE):
        return None
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None

def remove_sign_history():
    if os.path.exists(HISTORY_FILE):
        try:
            os.remove(HISTORY_FILE)
        except Exception:
            pass

def main():
    parser = argparse.ArgumentParser(description="Place/Undo Shop entrance sign")
    parser.add_argument("--text", default="SHOP", help="Text to display on sign (default: SHOP)")
    parser.add_argument("--facing", default="west", help="Sign facing direction (default: west)")
    parser.add_argument("--undo", action="store_true", help="Remove shop entrance sign (sets block to air)")
    parser.add_argument("--dry-run", action="store_true", help="Preview command without executing")

    args = parser.parse_args()

    # Sign location 1 block higher above entrance (X: 1293, Y: 81, Z: -218)
    x, y, z = 1293, 81, -218

    if args.undo:
        hist = load_sign_history()
        target_x = hist["coords"]["x"] if hist else x
        target_y = hist["coords"]["y"] if hist else y
        target_z = hist["coords"]["z"] if hist else z

        cmd = f"execute in minecraft:overworld run setblock {target_x} {target_y} {target_z} minecraft:air"
        print("🔄 Undoing shop entrance sign...")
        if send_exaroton_command(cmd, dry_run=args.dry_run):
            remove_sign_history()
            print("✨ Successfully removed shop entrance sign.")
        else:
            print("❌ Failed to remove shop entrance sign.")
    else:
        sign_text = args.text
        facing = args.facing
        # NBT data for Minecraft Oak Wall Sign
        sign_nbt = (
            'minecraft:oak_wall_sign[facing=' + facing + ']{'
            'front_text:{messages:[\'{"text":""}\',\'{"text":"=== ' + sign_text + ' ===","bold":true,"color":"dark_blue"}\',\'{"text":"Welcome!","italic":true,"color":"gold"}\',\'{"text":""}\']}'
            '}'
        )
        
        cmd = f"execute in minecraft:overworld run setblock {x} {y} {z} {sign_nbt} replace"
        print(f"🔨 Placing shop sign at ({x}, {y}, {z}) facing {facing}...")
        if send_exaroton_command(cmd, dry_run=args.dry_run):
            save_sign_history({"x": x, "y": y, "z": z}, sign_nbt)
            print("🎉 Shop entrance sign successfully created!")
        else:
            print("❌ Failed to place shop entrance sign.")

if __name__ == "__main__":
    main()
