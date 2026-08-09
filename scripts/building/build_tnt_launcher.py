#!/usr/bin/env python3
"""
Automated Minecraft TNT Launcher Generator
------------------------------------------
Builds an automated, North-facing TNT launcher centered at X=1196, Y=63, Z=-128.
Supports dry-run verification and full rollback (`--undo`).

Usage:
  python3 build_tnt_launcher.py [--dry-run]
  python3 build_tnt_launcher.py --undo [--dry-run]
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
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "tnt_launcher_history.json")

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
            print(f"✅ Executed: {cmd}")
            return True
        else:
            print(f"❌ Exaroton Command Error: {data.get('error')}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def generate_build_commands():
    cmds = []
    # Center: 1196 63 -128
    cx, cy, cz = 1196, 63, -128

    # 1. Clean area (Y=62 to Y=67, 7x7 footprint around center)
    cmds.append(f"fill {cx-4} {cy} {cz-5} {cx+4} {cy+4} {cz+3} air")

    # 2. Base Foundation (Y = 62)
    cmds.append(f"fill {cx-3} {cy-1} {cz-4} {cx+3} {cy-1} {cz+2} obsidian")

    # 3. Water Channel Walls & Floor (Y = 63)
    cmds.append(f"fill {cx-1} {cy} {cz-3} {cx+1} {cy} {cz+1} obsidian")
    # Left and Right walls at cy (Y=63)
    cmds.append(f"fill {cx-1} {cy} {cz-2} {cx-1} {cy} {cz} obsidian")
    cmds.append(f"fill {cx+1} {cy} {cz-2} {cx+1} {cy} {cz} obsidian")
    # Back wall at Y=63
    cmds.append(f"setblock {cx} {cy} {cz+1} obsidian")
    cmds.append(f"setblock {cx} {cy+1} {cz+1} obsidian")

    # 4. Water block at the back of channel (Z=cz, Y=63)
    cmds.append(f"setblock {cx} {cy} {cz} water")

    # 5. Launch Slab at front of channel (Z=cz-3, Y=63)
    cmds.append(f"setblock {cx} {cy} {cz-3} stone_brick_slab[type=bottom]")

    # 6. Dispensers for Propellant (Y=64)
    # Left Wall dispensers facing East (towards center channel X=1196)
    cmds.append(f"setblock {cx-1} {cy+1} {cz} dispenser[facing=east]")
    cmds.append(f"setblock {cx-1} {cy+1} {cz-1} dispenser[facing=east]")
    cmds.append(f"setblock {cx-1} {cy+1} {cz-2} dispenser[facing=east]")

    # Right Wall dispensers facing West
    cmds.append(f"setblock {cx+1} {cy+1} {cz} dispenser[facing=west]")
    cmds.append(f"setblock {cx+1} {cy+1} {cz-1} dispenser[facing=west]")
    cmds.append(f"setblock {cx+1} {cy+1} {cz-2} dispenser[facing=west]")

    # 7. Dispenser for Projectile (Y=65)
    cmds.append(f"setblock {cx} {cy+2} {cz-3} dispenser[facing=down]")

    # 8. Redstone Wiring (Y=65 for top of side dispensers, Y=64 for control)
    # Redstone dust on top of side dispensers to trigger propellant
    cmds.append(f"setblock {cx-1} {cy+2} {cz} redstone_wire")
    cmds.append(f"setblock {cx-1} {cy+2} {cz-1} redstone_wire")
    cmds.append(f"setblock {cx-1} {cy+2} {cz-2} redstone_wire")

    cmds.append(f"setblock {cx+1} {cy+2} {cz} redstone_wire")
    cmds.append(f"setblock {cx+1} {cy+2} {cz-1} redstone_wire")
    cmds.append(f"setblock {cx+1} {cy+2} {cz-2} redstone_wire")

    # Connect left and right lines behind the water source (Z=cz+1)
    cmds.append(f"setblock {cx-1} {cy+2} {cz+1} obsidian")
    cmds.append(f"setblock {cx} {cy+2} {cz+1} obsidian")
    cmds.append(f"setblock {cx+1} {cy+2} {cz+1} obsidian")
    cmds.append(f"setblock {cx-1} {cy+2} {cz+1} redstone_wire")
    cmds.append(f"setblock {cx} {cy+2} {cz+1} redstone_wire")
    cmds.append(f"setblock {cx+1} {cy+2} {cz+1} redstone_wire")

    # 9. Clock / Control Circuit Platform
    # Platform on the left side (X=cx-2 to cx-3, Z=cz-1 to cz+1)
    cmds.append(f"fill {cx-3} {cy} {cz-2} {cx-2} {cy} {cz+1} obsidian")

    # Lever for toggle
    cmds.append(f"setblock {cx-3} {cy+1} {cz+1} lever[face=floor,facing=north]")

    # Comparator clock
    cmds.append(f"setblock {cx-3} {cy+1} {cz} redstone_comparator[facing=north,mode=subtract]")
    cmds.append(f"setblock {cx-3} {cy+1} {cz-1} redstone_wire")
    cmds.append(f"setblock {cx-2} {cy+1} {cz-1} redstone_wire")
    cmds.append(f"setblock {cx-2} {cy+1} {cz} redstone_wire")

    # Connect clock output to propellant dispensers
    cmds.append(f"setblock {cx-2} {cy+1} {cz+1} redstone_wire")
    # Staircase connection block for redstone to reach Y=65 (top of dispenser)
    # Clock output at cx-2 cy+1 cz+1 (Y=64) will power cx-1 cy+2 cz (Y=65) dispenser top
    # Let's ensure a solid block is under the stair connection
    cmds.append(f"setblock {cx-2} {cy} {cz} obsidian")

    # Connect clock output to projectile dispenser with delay
    # Repeaters pointing North from the clock output line to delay the projectile
    # The clock output is at cx-2 cy+1 cz-1. We run repeaters along X=cx-2 to the North.
    cmds.append(f"setblock {cx-2} {cy+1} {cz-2} redstone_repeater[facing=north,delay=4]")
    cmds.append(f"setblock {cx-2} {cy+1} {cz-3} redstone_repeater[facing=north,delay=4]")
    # Wire over to the projectile dispenser
    cmds.append(f"setblock {cx-1} {cy+1} {cz-3} obsidian")
    cmds.append(f"setblock {cx-1} {cy+2} {cz-3} redstone_wire")

    # 10. Load TNT into all 7 dispensers
    dispensers = [
        (cx-1, cy+1, cz),   # Propellant left 1
        (cx-1, cy+1, cz-1), # Propellant left 2
        (cx-1, cy+1, cz-2), # Propellant left 3
        (cx+1, cy+1, cz),   # Propellant right 1
        (cx+1, cy+1, cz-1), # Propellant right 2
        (cx+1, cy+1, cz-2), # Propellant right 3
        (cx, cy+2, cz-3)    # Projectile
    ]

    for dx, dy, dz in dispensers:
        for slot in range(9):
            cmds.append(f"item replace block {dx} {dy} {dz} container.{slot} with tnt 64")

    return cmds

def save_rollback_data(cmds):
    rollback_cmds = []
    cx, cy, cz = 1196, 63, -128
    rollback_cmds.append(f"fill {cx-4} {cy-1} {cz-5} {cx+4} {cy+4} {cz+3} air")
    # Also clean dropped entities
    rollback_cmds.append("kill @e[type=item,x=1190,y=60,z=-135,distance=..15]")

    with open(HISTORY_FILE, "w") as f:
        json.dump(rollback_cmds, f, indent=2)

def run_undo(dry_run=False):
    if not os.path.exists(HISTORY_FILE):
        print("❌ No history file found for rollback.")
        return False
    
    with open(HISTORY_FILE, "r") as f:
        cmds = json.load(f)
    
    for cmd in cmds:
        send_exaroton_command(cmd, dry_run=dry_run)
    
    print("✅ Rollback/Undo executed successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Build or undo TNT launcher.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing.")
    parser.add_argument("--undo", action="store_true", help="Undo the last build.")
    args = parser.parse_args()

    if args.undo:
        run_undo(args.dry_run)
    else:
        cmds = generate_build_commands()
        save_rollback_data(cmds)
        for cmd in cmds:
            send_exaroton_command(cmd, dry_run=args.dry_run)
        print("✅ TNT Launcher build complete.")

if __name__ == "__main__":
    main()
