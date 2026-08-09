#!/usr/bin/env python3
"""
Build a single-story house using normal, easily available materials (Oak Logs, Stone Bricks, Oak Planks, Glass)
strictly inside the South Main Base Red region of Azan Saleh's plot (azansalehhh).

Region Bounds (South Red Base):
X: 1244 to 1255 (Width = 12 blocks)
Z: -204 to -191 (Length = 14 blocks)
Y Floor: 62 (Preserved Red Concrete floor)
House Height: Y = 63 to 68

Footprint: 10x12 blocks (X: 1245..1254, Z: -203..-192)

Supports --dry-run and --undo options.
"""

import os
import sys
import json
import subprocess
import argparse

BACKUP_FILE = "azansaleh_red_house_history.json"

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

MIN_X, MAX_X = 1245, 1254
MIN_Z, MAX_Z = -203, -192

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

def build_single_story_house(dry_run=False):
    print("=== Building Single-Story House in South Red Region (Azan Saleh) ===")
    
    cmds = []
    
    # 0. Clear volume above floor (Y=63 to 68)
    cmds.append(f"fill 1244 63 -204 1255 68 -191 minecraft:air")
    
    # 1. Corner Support Pillars (Oak Log Y=63 to 66)
    cmds.append(f"fill {MIN_X} 63 {MIN_Z} {MIN_X} 66 {MIN_Z} minecraft:oak_log")
    cmds.append(f"fill {MAX_X} 63 {MIN_Z} {MAX_X} 66 {MIN_Z} minecraft:oak_log")
    cmds.append(f"fill {MIN_X} 63 {MAX_Z} {MIN_X} 66 {MAX_Z} minecraft:oak_log")
    cmds.append(f"fill {MAX_X} 63 {MAX_Z} {MAX_X} 66 {MAX_Z} minecraft:oak_log")
    
    # 2. Lower Foundation Ring (Stone Bricks Y=63)
    cmds.append(f"fill {MIN_X} 63 {MIN_Z} {MAX_X} 63 {MIN_Z} minecraft:stone_bricks") # North
    cmds.append(f"fill {MIN_X} 63 {MAX_Z} {MAX_X} 63 {MAX_Z} minecraft:stone_bricks") # South
    cmds.append(f"fill {MIN_X} 63 {MIN_Z} {MIN_X} 63 {MAX_Z} minecraft:stone_bricks") # West
    cmds.append(f"fill {MAX_X} 63 {MIN_Z} {MAX_X} 63 {MAX_Z} minecraft:stone_bricks") # East

    # 3. Main Wall Construction (Oak Planks Y=64 to 66)
    cmds.append(f"fill {MIN_X} 64 {MIN_Z} {MAX_X} 66 {MIN_Z} minecraft:oak_planks outline") # North Wall
    cmds.append(f"fill {MIN_X} 64 {MAX_Z} {MAX_X} 66 {MAX_Z} minecraft:oak_planks outline") # South Wall
    cmds.append(f"fill {MIN_X} 64 {MIN_Z} {MIN_X} 66 {MAX_Z} minecraft:oak_planks outline") # West Wall
    cmds.append(f"fill {MAX_X} 64 {MIN_Z} {MAX_X} 66 {MAX_Z} minecraft:oak_planks outline") # East Wall

    # 4. Glass Panes Windows (Y=64 to 65)
    cmds.append(f"fill {MIN_X} 64 -199 {MIN_X} 65 -196 minecraft:glass_pane") # West Windows
    cmds.append(f"fill {MAX_X} 64 -199 {MAX_X} 65 -196 minecraft:glass_pane") # East Windows
    cmds.append(f"fill 1248 64 {MIN_Z} 1251 65 {MIN_Z} minecraft:glass_pane") # North Windows

    # 5. Front Entrance Doorway (South Wall Z=-192, X=1249)
    cmds.append(f"setblock 1249 63 {MAX_Z} minecraft:air")
    cmds.append(f"setblock 1249 64 {MAX_Z} minecraft:air")
    cmds.append(f"setblock 1249 63 {MAX_Z} minecraft:oak_door[half=lower,facing=south]")
    cmds.append(f"setblock 1249 64 {MAX_Z} minecraft:oak_door[half=upper,facing=south]")

    # 6. Roof Structure (Y=67 to 68) - Overhang Oak Slabs & Roof Cap
    cmds.append(f"fill {MIN_X-1} 67 {MIN_Z-1} {MAX_X+1} 67 {MAX_Z+1} minecraft:oak_slab[type=bottom]")
    cmds.append(f"fill {MIN_X} 68 {MIN_Z} {MAX_X} 68 {MAX_Z} minecraft:oak_slab[type=top]")

    # 7. Interior Lighting (Lanterns Y=66)
    cmds.append(f"setblock 1249 66 -197 minecraft:lantern[hanging=true]")
    cmds.append(f"setblock 1250 66 -197 minecraft:lantern[hanging=true]")

    history = []
    for cmd in cmds:
        print(f"Executing: {cmd}")
        success = send_exaroton_command(cmd, dry_run=dry_run)
        if success:
            history.append(cmd)

    if not dry_run:
        with open(BACKUP_FILE, "w") as f:
            json.dump({"applied_commands": history}, f, indent=2)
        print(f"Single-story house built successfully! Saved history to {BACKUP_FILE}")

def undo(dry_run=False):
    print("Undoing single-story house build (clearing Y=63 to 68)...")
    cmd = f"fill 1244 63 -204 1255 68 -191 minecraft:air"
    send_exaroton_command(cmd, dry_run=dry_run)
    print("House structure cleared successfully.")

def main():
    parser = argparse.ArgumentParser(description="Build single-story house in South Red region")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--undo", action="store_true", help="Undo house construction")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        build_single_story_house(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
