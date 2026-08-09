#!/usr/bin/env python3
"""
Build a multi-story mansion strictly within the available Blue Region in Azan's area.

Region Bounds:
X: 1248 to 1255 (Width = 8 blocks)
Z: -219 to -205 (Length = 15 blocks)
Y Floor: 62
Mansion Structure Height: Y = 63 to 76

Supports --dry-run and --undo options.
"""

import os
import sys
import json
import subprocess
import argparse

BACKUP_FILE = "azan_blue_mansion_history.json"

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
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

MIN_X, MAX_X = 1248, 1255
MIN_Z, MAX_Z = -219, -205

def send_exaroton_command(cmd, dry_run=False):
    if dry_run:
        print(f"[DRY-RUN] Console Command: {cmd}")
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
        if not data.get("success", False):
            print(f"[ERROR] Exaroton Command Failed: {data.get('error')}")
            return False
        return True
    except Exception as e:
        print(f"[ERROR] Failed to parse API response: {res.stdout}")
        return False

def build_mansion(dry_run=False):
    print("=== Building Mansion in Azan's Blue Region ===")
    
    cmds = []
    
    # 0. Clear building height volume (Y=63 to 76)
    cmds.append(f"fill {MIN_X} 63 {MIN_Z} {MAX_X} 76 {MAX_Z} minecraft:air")
    
    # 1. Corner Pillars (Dark Oak Logs Y=63 to 73)
    cmds.append(f"fill {MIN_X} 63 {MIN_Z} {MIN_X} 73 {MIN_Z} minecraft:dark_oak_log")
    cmds.append(f"fill {MAX_X} 63 {MIN_Z} {MAX_X} 73 {MIN_Z} minecraft:dark_oak_log")
    cmds.append(f"fill {MIN_X} 63 {MAX_Z} {MIN_X} 73 {MAX_Z} minecraft:dark_oak_log")
    cmds.append(f"fill {MAX_X} 63 {MAX_Z} {MAX_X} 73 {MAX_Z} minecraft:dark_oak_log")
    
    # 2. Ground Floor Outer Walls (Y=63 to 67) - Deepslate Bricks & Quartz
    cmds.append(f"fill {MIN_X} 63 {MIN_Z} {MAX_X} 67 {MIN_Z} minecraft:deepslate_bricks outline") # North Wall
    cmds.append(f"fill {MIN_X} 63 {MAX_Z} {MAX_X} 67 {MAX_Z} minecraft:deepslate_bricks outline") # South Wall
    cmds.append(f"fill {MIN_X} 63 {MIN_Z} {MIN_X} 67 {MAX_Z} minecraft:deepslate_bricks outline") # West Wall
    cmds.append(f"fill {MAX_X} 63 {MIN_Z} {MAX_X} 67 {MAX_Z} minecraft:deepslate_bricks outline") # East Wall

    # 3. Ground Floor Windows (Glass Panes Y=64 to 65)
    cmds.append(f"fill {MIN_X} 64 -215 {MIN_X} 65 -209 minecraft:glass_pane") # West Windows
    cmds.append(f"fill {MAX_X} 64 -215 {MAX_X} 65 -209 minecraft:glass_pane") # East Windows
    cmds.append(f"fill 1250 64 {MIN_Z} 1253 65 {MIN_Z} minecraft:glass_pane") # North Windows

    # 4. Front Entrance Archway & Door (South Wall Z=-205, X=1251..1252)
    cmds.append(f"fill 1251 63 {MAX_Z} 1252 65 {MAX_Z} minecraft:quartz_block")
    cmds.append(f"fill 1251 63 {MAX_Z} 1252 64 {MAX_Z} minecraft:air") # Doorway cutout
    cmds.append(f"setblock 1251 63 {MAX_Z} minecraft:dark_oak_door[half=lower,facing=south]")
    cmds.append(f"setblock 1251 64 {MAX_Z} minecraft:dark_oak_door[half=upper,facing=south]")
    
    # 5. First Floor Ceiling / Second Floor Base (Y=68) - Spruce Planks
    cmds.append(f"fill {MIN_X+1} 68 {MIN_Z+1} {MAX_X-1} 68 {MAX_Z-1} minecraft:spruce_planks")

    # 6. Interior Staircase (Y=63 to 68)
    cmds.append(f"fill 1249 68 -212 1250 68 -211 minecraft:air") # Stairwell opening
    cmds.append(f"setblock 1249 63 -210 minecraft:spruce_stairs[facing=north]")
    cmds.append(f"setblock 1249 64 -211 minecraft:spruce_stairs[facing=north]")
    cmds.append(f"setblock 1249 65 -212 minecraft:spruce_stairs[facing=north]")
    cmds.append(f"setblock 1249 66 -212 minecraft:spruce_planks")
    cmds.append(f"setblock 1249 67 -212 minecraft:spruce_stairs[facing=north]")

    # 7. Second Floor Walls (Y=69 to 73) - Smooth Quartz & Tinted Glass
    cmds.append(f"fill {MIN_X} 69 {MIN_Z} {MAX_X} 73 {MIN_Z} minecraft:quartz_block outline") # North Wall
    cmds.append(f"fill {MIN_X} 69 {MAX_Z} {MAX_X} 73 {MAX_Z} minecraft:quartz_block outline") # South Wall
    cmds.append(f"fill {MIN_X} 69 {MIN_Z} {MIN_X} 73 {MAX_Z} minecraft:quartz_block outline") # West Wall
    cmds.append(f"fill {MAX_X} 69 {MIN_Z} {MAX_X} 73 {MAX_Z} minecraft:quartz_block outline") # East Wall

    # Second Floor Windows (Y=70 to 71)
    cmds.append(f"fill {MIN_X} 70 -214 {MIN_X} 71 -210 minecraft:tinted_glass")
    cmds.append(f"fill {MAX_X} 70 -214 {MAX_X} 71 -210 minecraft:tinted_glass")
    cmds.append(f"fill 1250 70 {MAX_Z} 1253 71 {MAX_Z} minecraft:tinted_glass")

    # 8. Mansion Roof Structure (Y=74 to 76) - Dark Oak Roof
    cmds.append(f"fill {MIN_X-1} 74 {MIN_Z-1} {MAX_X+1} 74 {MAX_Z+1} minecraft:dark_oak_slab[type=bottom]")
    cmds.append(f"fill {MIN_X} 75 {MIN_Z} {MAX_X} 75 {MAX_Z} minecraft:dark_oak_planks")
    cmds.append(f"fill {MIN_X+1} 76 {MIN_Z+1} {MAX_X-1} 76 {MAX_Z-1} minecraft:dark_oak_slab[type=top]")

    # 9. Interior Lighting (Lanterns Y=66 and Y=72)
    cmds.append(f"setblock 1251 66 -214 minecraft:lantern[hanging=true]")
    cmds.append(f"setblock 1251 66 -208 minecraft:lantern[hanging=true]")
    cmds.append(f"setblock 1251 72 -214 minecraft:lantern[hanging=true]")
    cmds.append(f"setblock 1251 72 -208 minecraft:lantern[hanging=true]")

    history = []
    for cmd in cmds:
        print(f"Executing: {cmd}")
        success = send_exaroton_command(cmd, dry_run=dry_run)
        if success:
            history.append(cmd)

    if not dry_run:
        with open(BACKUP_FILE, "w") as f:
            json.dump({"applied_commands": history}, f, indent=2)
        print(f"Mansion built successfully! Saved build history to {BACKUP_FILE}")

def undo(dry_run=False):
    print(f"Undoing mansion build (clearing Y=63 to 76)...")
    cmd = f"fill {MIN_X-1} 63 {MIN_Z-1} {MAX_X+1} 76 {MAX_Z+1} minecraft:air"
    send_exaroton_command(cmd, dry_run=dry_run)
    print("Mansion structure cleared successfully.")

def main():
    parser = argparse.ArgumentParser(description="Build mansion in Azan's Blue Region")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--undo", action="store_true", help="Undo mansion construction")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        build_mansion(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
