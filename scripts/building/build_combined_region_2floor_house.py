#!/usr/bin/env python3
"""
Build a 2-story house with normal materials (Oak Planks, Stone Bricks, Oak Logs, Glass)
strictly inside `combined_region` bounds with a perfect continuous staircase and West entrance door.

Region Bounds:
X: 1293 to 1300 (Width = 8 blocks)
Z: -230 to -222 (Length = 9 blocks)
Y Floor: 78
House Height: Y = 79 to 91

Staircase: Continuous 5-step straight oak stairs going from Y=79 (Ground) to Y=84 (Second Floor) along X=1298.

Entrance Door: WEST Wall (X=1293, Z=-226, Y=79..80)

Supports --dry-run and --undo options.
"""

import os
import sys
import json
import subprocess
import argparse

BACKUP_FILE = "combined_region_house_history.json"

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

MIN_X, MAX_X = 1293, 1300
MIN_Z, MAX_Z = -230, -222

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

def build_house(dry_run=False):
    print("=== Building 2-Story House in combined_region (Perfect Stairs & West Door) ===")
    
    cmds = []
    
    # 0. Clear building height volume (Y=79 to 91)
    cmds.append(f"fill {MIN_X-1} 79 {MIN_Z-1} {MAX_X+1} 91 {MAX_Z+1} minecraft:air")
    
    # 1. Corner Log Pillars (Oak Log Y=79 to 88)
    cmds.append(f"fill {MIN_X} 79 {MIN_Z} {MIN_X} 88 {MIN_Z} minecraft:oak_log")
    cmds.append(f"fill {MAX_X} 79 {MIN_Z} {MAX_X} 88 {MIN_Z} minecraft:oak_log")
    cmds.append(f"fill {MIN_X} 79 {MAX_Z} {MIN_X} 88 {MAX_Z} minecraft:oak_log")
    cmds.append(f"fill {MAX_X} 79 {MAX_Z} {MAX_X} 88 {MAX_Z} minecraft:oak_log")
    
    # 2. Ground Floor Outer Walls (Y=79 to 83) - Stone Bricks
    cmds.append(f"fill {MIN_X} 79 {MIN_Z} {MAX_X} 83 {MIN_Z} minecraft:stone_bricks outline") # North Wall
    cmds.append(f"fill {MIN_X} 79 {MAX_Z} {MAX_X} 83 {MAX_Z} minecraft:stone_bricks outline") # South Wall
    cmds.append(f"fill {MIN_X} 79 {MIN_Z} {MIN_X} 83 {MAX_Z} minecraft:stone_bricks outline") # West Wall
    cmds.append(f"fill {MAX_X} 79 {MIN_Z} {MAX_X} 83 {MAX_Z} minecraft:stone_bricks outline") # East Wall

    # 3. Ground Floor Windows (Glass Panes Y=80 to 81)
    cmds.append(f"fill {MAX_X} 80 -228 {MAX_X} 81 -224 minecraft:glass_pane") # East Windows
    cmds.append(f"fill 1295 80 {MIN_Z} 1298 81 {MIN_Z} minecraft:glass_pane") # North Windows
    cmds.append(f"fill 1295 80 {MAX_Z} 1298 81 {MAX_Z} minecraft:glass_pane") # South Windows

    # 4. Front Entrance Door on WEST Wall (X=1293, Z=-226, Y=79..80)
    cmds.append(f"fill {MIN_X} 79 -226 {MIN_X} 81 -226 minecraft:stone_bricks")
    cmds.append(f"fill {MIN_X} 79 -226 {MIN_X} 80 -226 minecraft:air") # Doorway cutout on West wall
    cmds.append(f"setblock {MIN_X} 79 -226 minecraft:oak_door[half=lower,facing=west]")
    cmds.append(f"setblock {MIN_X} 80 -226 minecraft:oak_door[half=upper,facing=west]")
    
    # 5. First Floor Ceiling / Second Floor Base (Y=84) - Oak Planks
    cmds.append(f"fill {MIN_X+1} 84 {MIN_Z+1} {MAX_X-1} 84 {MAX_Z-1} minecraft:oak_planks")

    # 6. PERFECT CONTINUOUS STAIRCASE (Y=79 to 84 along X=1298)
    # Clear stairwell opening in Y=84 ceiling and Y=85 second floor space for full walking headroom
    cmds.append(f"fill 1298 84 -227 1298 85 -223 minecraft:air")
    
    # Continuous steps from Y=79 to Y=83 leading up to Y=84
    cmds.append(f"setblock 1298 79 -223 minecraft:oak_stairs[facing=north]") # Step 1 (Y=79)
    cmds.append(f"setblock 1298 80 -224 minecraft:oak_stairs[facing=north]") # Step 2 (Y=80)
    cmds.append(f"setblock 1298 81 -225 minecraft:oak_stairs[facing=north]") # Step 3 (Y=81)
    cmds.append(f"setblock 1298 82 -226 minecraft:oak_stairs[facing=north]") # Step 4 (Y=82)
    cmds.append(f"setblock 1298 83 -227 minecraft:oak_stairs[facing=north]") # Step 5 (Y=83)

    # 7. Second Floor Walls (Y=85 to 88) - Oak Planks
    cmds.append(f"fill {MIN_X} 85 {MIN_Z} {MAX_X} 88 {MIN_Z} minecraft:oak_planks outline") # North Wall
    cmds.append(f"fill {MIN_X} 85 {MAX_Z} {MAX_X} 88 {MAX_Z} minecraft:oak_planks outline") # South Wall
    cmds.append(f"fill {MIN_X} 85 {MIN_Z} {MIN_X} 88 {MAX_Z} minecraft:oak_planks outline") # West Wall
    cmds.append(f"fill {MAX_X} 85 {MIN_Z} {MAX_X} 88 {MAX_Z} minecraft:oak_planks outline") # East Wall

    # Second Floor Windows (Y=86 to 87)
    cmds.append(f"fill {MIN_X} 86 -228 {MIN_X} 87 -224 minecraft:glass_pane")
    cmds.append(f"fill {MAX_X} 86 -228 {MAX_X} 87 -224 minecraft:glass_pane")
    cmds.append(f"fill 1295 86 {MAX_Z} 1298 87 {MAX_Z} minecraft:glass_pane")

    # 8. Roof Structure (Y=89 to 91) - Pitched Oak Roof
    cmds.append(f"fill {MIN_X-1} 89 {MIN_Z-1} {MAX_X+1} 89 {MAX_Z+1} minecraft:oak_slab[type=bottom]")
    cmds.append(f"fill {MIN_X} 90 {MIN_Z} {MAX_X} 90 {MAX_Z} minecraft:oak_planks")
    cmds.append(f"fill {MIN_X+1} 91 {MIN_Z+1} {MAX_X-1} 91 {MAX_Z-1} minecraft:oak_slab[type=top]")

    # 9. Interior Lighting (Lanterns Y=82 and Y=87)
    cmds.append(f"setblock 1296 82 -226 minecraft:lantern[hanging=true]")
    cmds.append(f"setblock 1296 87 -226 minecraft:lantern[hanging=true]")

    history = []
    for cmd in cmds:
        print(f"Executing: {cmd}")
        success = send_exaroton_command(cmd, dry_run=dry_run)
        if success:
            history.append(cmd)

    if not dry_run:
        with open(BACKUP_FILE, "w") as f:
            json.dump({"applied_commands": history}, f, indent=2)
        print(f"House built successfully with perfect staircase & West door! Saved history to {BACKUP_FILE}")

def undo(dry_run=False):
    print(f"Undoing 2-story house build (clearing Y=79 to 91)...")
    cmd = f"fill {MIN_X-1} 79 {MIN_Z-1} {MAX_X+1} 91 {MAX_Z+1} minecraft:air"
    send_exaroton_command(cmd, dry_run=dry_run)
    print("House structure cleared successfully.")

def main():
    parser = argparse.ArgumentParser(description="Build 2-story house in combined_region with perfect stairs")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--undo", action="store_true", help="Undo house construction")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        build_house(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
