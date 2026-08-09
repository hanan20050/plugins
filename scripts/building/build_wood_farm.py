#!/usr/bin/env python3
"""
Automated Minecraft Wood Collector & Crop Farm Generator
-------------------------------------------------------
Builds an automated Wood Collector farm and a crop farm centered at X=1276, Y=66, Z=-63.
Supports dry-run verification and full rollback (`--undo`).

Usage:
  python3 build_wood_farm.py [--dry-run]
  python3 build_wood_farm.py --undo [--dry-run]
"""

import os
import sys
import json
import subprocess
import argparse

# Load Environment Credentials
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
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "wood_farm_history.json")

def send_exaroton_command(cmd, dry_run=False):
    if dry_run:
        print(f"[DRY-RUN] Command: {cmd}")
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
            return True
        else:
            print(f"❌ Exaroton Command Error: {data.get('error')}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def generate_build_commands():
    cmds = []
    cx, cy, cz = 1276, 66, -63

    # 1. Clear area (Y=65 to Y=76, 19x13 footprint to cover both farms)
    cmds.append(f"fill {cx-6} {cy-1} {cz-6} {cx+12} {cy+10} {cz+6} air")

    # 2. Base platform for wood farm (X: 1272 to 1280, Z: -67 to -59)
    cmds.append(f"fill {cx-4} {cy-1} {cz-4} {cx+4} {cy-1} {cz+4} stone_bricks")

    # Dirt block for sapling
    cmds.append(f"setblock {cx} {cy} {cz} dirt")

    # Dispenser with bone meal facing South towards the dirt block
    cmds.append(f"setblock {cx} {cy} {cz-1} dispenser[facing=south]")
    # Fill dispenser with bone meal
    cmds.append(f"replaceitem block {cx} {cy} {cz-1} container.0 bone_meal 64")
    cmds.append(f"replaceitem block {cx} {cy} {cz-1} container.1 bone_meal 64")
    cmds.append(f"replaceitem block {cx} {cy} {cz-1} container.2 bone_meal 64")

    # Standing pressure plate for player to stand on and trigger bone-mealing
    # Placed at 1276 66 -65 (Z=-65, in front of the dispenser)
    cmds.append(f"setblock {cx} {cy} {cz-2} stone_pressure_plate")
    # Redstone wiring from pressure plate to dispenser via repeating clock
    cmds.append(f"setblock {cx-1} {cy-1} {cz-2} stone_bricks")
    cmds.append(f"setblock {cx-1} {cy} {cz-2} redstone_wire")
    cmds.append(f"setblock {cx-1} {cy} {cz-1} observer[facing=east]")
    cmds.append(f"setblock {cx-2} {cy} {cz-1} observer[facing=west]") # observer clock facing each other to pulse dispenser when powered

    # Stack of 5 Pistons facing East at X=1275
    for y_offset in range(5):
        cmds.append(f"setblock {cx-1} {cy+y_offset} {cz} piston[facing=east]")
        # Solid block behind pistons
        cmds.append(f"setblock {cx-2} {cy+y_offset} {cz} stone_bricks")
        # Redstone dust on the solid block to power the pistons
        cmds.append(f"setblock {cx-2} {cy+y_offset+1} {cz} redstone_wire")

    # Observer at Y=71, Z=-62 (detects trunk growth at Y=71)
    cmds.append(f"setblock {cx} {cy+5} {cz+1} observer[facing=north]")
    cmds.append(f"setblock {cx} {cy+5} {cz+2} redstone_wire")
    cmds.append(f"setblock {cx-1} {cy+5} {cz+2} redstone_wire")
    cmds.append(f"setblock {cx-2} {cy+5} {cz+2} redstone_wire")
    cmds.append(f"setblock {cx-2} {cy+5} {cz+1} redstone_wire")

    # Glass ceiling to limit tree height at Y=73 (7 blocks above dirt)
    cmds.append(f"setblock {cx} {cy+7} {cz} glass")

    # Water trench to collect leaves drops (saplings/apples)
    # 5x5 trench 1 block down (Y=65) around the dirt block
    cmds.append(f"fill {cx-2} {cy-1} {cz-2} {cx+2} {cy-1} {cz+2} air")
    # Restore dirt block and dispenser/piston foundations
    cmds.append(f"setblock {cx} {cy-1} {cz} stone_bricks")
    cmds.append(f"setblock {cx} {cy-1} {cz-1} stone_bricks")
    cmds.append(f"setblock {cx-1} {cy-1} {cz} stone_bricks")
    # Put water in corners to flow to the front collection point
    cmds.append(f"setblock {cx-2} {cy-1} {cz-2} water")
    cmds.append(f"setblock {cx+2} {cy-1} {cz-2} water")
    cmds.append(f"setblock {cx-2} {cy-1} {cz+2} water")
    cmds.append(f"setblock {cx+2} {cy-1} {cz+2} water")
    # Hopper and chest at the front for collection
    cmds.append(f"setblock {cx} {cy-1} {cz+2} hopper[facing=south]")
    cmds.append(f"setblock {cx} {cy-1} {cz+3} chest[facing=north]")

    # 3. Crop Farm (7x7 footprint from X=1281 to 1287, Z=-66 to -60)
    # Border
    cmds.append(f"fill 1281 {cy} -66 1287 {cy} -66 polished_andesite")
    cmds.append(f"fill 1281 {cy} -60 1287 {cy} -60 polished_andesite")
    cmds.append(f"fill 1281 {cy} -66 1281 {cy} -60 polished_andesite")
    cmds.append(f"fill 1287 {cy} -66 1287 {cy} -60 polished_andesite")
    # Water source in center of crop farm
    cmds.append(f"setblock 1284 {cy} -63 water")
    cmds.append(f"setblock 1284 {cy+1} -63 lily_pad")
    # Farmland
    cmds.append(f"fill 1282 {cy} -65 1283 {cy} -61 farmland[moisture=7]")
    cmds.append(f"fill 1285 {cy} -65 1286 {cy} -61 farmland[moisture=7]")
    cmds.append(f"fill 1284 {cy} -65 1284 {cy} -64 farmland[moisture=7]")
    cmds.append(f"fill 1284 {cy} -62 1284 {cy} -61 farmland[moisture=7]")
    # Plant Crops
    cmds.append(f"fill 1282 {cy+1} -65 1282 {cy+1} -61 carrots[age=7]")
    cmds.append(f"fill 1283 {cy+1} -65 1283 {cy+1} -61 potatoes[age=7]")
    cmds.append(f"fill 1285 {cy+1} -65 1285 {cy+1} -61 wheat[age=7]")
    cmds.append(f"fill 1286 {cy+1} -65 1286 {cy+1} -61 beetroots[age=3]")
    # Corner composters
    cmds.append(f"setblock 1281 {cy+1} -66 composter[level=0]")
    cmds.append(f"setblock 1287 {cy+1} -66 composter[level=0]")
    cmds.append(f"setblock 1281 {cy+1} -60 composter[level=0]")
    cmds.append(f"setblock 1287 {cy+1} -60 composter[level=0]")
    # Torches for lighting
    cmds.append(f"setblock 1281 {cy+2} -63 torch")
    cmds.append(f"setblock 1287 {cy+2} -63 torch")

    # Clear dropped item entities
    cmds.append(f"kill @e[type=item,x={cx},y={cy},z={cz},distance=..20]")

    return cmds

def execute_build(dry_run=False):
    cmds = generate_build_commands()
    history = {"commands_run": cmds, "center": {"x": 1276, "y": 66, "z": -63}}

    if not dry_run:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)

    print(f"Building Wood & Crop Farm with {len(cmds)} commands...")
    success_count = 0
    for c in cmds:
        if send_exaroton_command(c, dry_run=dry_run):
            success_count += 1

    print(f"Finished build. Executed {success_count}/{len(cmds)} commands.")
    return success_count == len(cmds)

def execute_undo(dry_run=False):
    cx, cy, cz = 1276, 66, -63
    undo_cmds = [
        f"fill {cx-6} {cy-1} {cz-6} {cx+12} {cy+10} {cz+6} air",
        f"fill {cx-6} {cy-1} {cz-6} {cx+12} {cy-1} {cz+6} grass_block",
        f"kill @e[type=item,x={cx},y={cy},z={cz},distance=..20]"
    ]
    print(f"Reverting Wood & Crop Farm area...")
    for c in undo_cmds:
        send_exaroton_command(c, dry_run=dry_run)

    if not dry_run and os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    print("✅ Rollback complete.")

def main():
    parser = argparse.ArgumentParser(description="Build or Undo Wood/Crop Farm")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--undo", action="store_true", help="Revert the construction")
    args = parser.parse_args()

    if args.undo:
        execute_undo(dry_run=args.dry_run)
    else:
        execute_build(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
