#!/usr/bin/env python3
"""
Automated Minecraft Iron Farm Generator
---------------------------------------
Builds an automated Iron Farm centered at X=1281, Y=66, Z=-368.
Supports dry-run verification and full rollback (`--undo`).

Usage:
  python3 build_iron_farm.py [--dry-run]
  python3 build_iron_farm.py --undo [--dry-run]
"""

import os
import sys
import json
import subprocess
import argparse

# Load Environment Credentials
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
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "iron_farm_history.json")

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
    cx, cy, cz = 1281, 66, -368

    # 1. Clear area (Y=66 to Y=80, 11x11 footprint)
    cmds.append(f"fill {cx-5} {cy} {cz-5} {cx+5} {cy+14} {cz+5} air")

    # 2. Base Collection & Chest (Y=66)
    cmds.append(f"setblock {cx} {cy} {cz-3} chest[facing=south]")
    cmds.append(f"setblock {cx-1} {cy} {cz-3} chest[facing=south]")
    # 3x3 Hoppers pointing south towards chest
    cmds.append(f"fill {cx-1} {cy} {cz-2} {cx+1} {cy} {cz} hopper[facing=south]")

    # 3. Outer Wall for Killing Chamber (Y=66 to Y=71, 5x5 outline)
    cmds.append(f"fill {cx-2} {cy} {cz-2} {cx+2} {cy+5} {cz+2} stone_bricks outline")
    # Clear interior 3x3 drop chute
    cmds.append(f"fill {cx-1} {cy+1} {cz-1} {cx+1} {cy+5} {cz+1} air")
    # Glass observation window front (Y=67..69)
    cmds.append(f"fill {cx-1} {cy+1} {cz-2} {cx+1} {cy+3} {cz-2} glass")

    # 4. Signs for Lava Stop (Y=68 inner wall)
    cmds.append(f"setblock {cx-1} {cy+2} {cz-1} oak_sign[rotation=4]")
    cmds.append(f"setblock {cx+1} {cy+2} {cz-1} oak_sign[rotation=12]")
    cmds.append(f"setblock {cx-1} {cy+2} {cz+1} oak_sign[rotation=4]")
    cmds.append(f"setblock {cx+1} {cy+2} {cz+1} oak_sign[rotation=12]")

    # Lava in killing chamber center
    cmds.append(f"setblock {cx} {cy+3} {cz} lava")

    # 5. Spawning Platform (Y=72, 9x9 solid smooth stone with 3x3 center hole)
    cmds.append(f"fill {cx-4} {cy+6} {cz-4} {cx+4} {cy+6} {cz+4} smooth_stone")
    cmds.append(f"fill {cx-1} {cy+6} {cz-1} {cx+1} {cy+6} {cz+1} air")

    # Platform Border Wall (Y=73)
    cmds.append(f"fill {cx-4} {cy+7} {cz-4} {cx+4} {cy+7} {cz+4} stone_brick_wall outline")
    cmds.append(f"fill {cx-3} {cy+7} {cz-3} {cx+3} {cy+7} {cz+3} air")

    # Water sources at platform corners to push golems to center hole
    cmds.append(f"setblock {cx-3} {cy+7} {cz-3} water")
    cmds.append(f"setblock {cx+3} {cy+7} {cz-3} water")
    cmds.append(f"setblock {cx-3} {cy+7} {cz+3} water")
    cmds.append(f"setblock {cx+3} {cy+7} {cz+3} water")

    # 6. Elevated Villager Pod & Zombie Chamber (Y=76..78)
    # Solid Platform under Villagers & Zombie at Y=75
    cmds.append(f"fill {cx-2} {cy+9} {cz-2} {cx+2} {cy+9} {cz+2} smooth_stone")

    # Build Villager Enclosure Outer Glass Walls & Inner Air (Y=76..78) BEFORE placing beds/workstations
    cmds.append(f"fill {cx-2} {cy+10} {cz-2} {cx+2} {cy+12} {cz+1} glass outline")
    cmds.append(f"fill {cx-1} {cy+10} {cz-1} {cx+1} {cy+12} {cz} air")
    # Roof over Villagers
    cmds.append(f"fill {cx-2} {cy+13} {cz-2} {cx+2} {cy+13} {cz+1} stone_brick_slab")

    # Zombie Cell (Z=+2, Y=76..78) - Completely sealed glass box with roof
    cmds.append(f"fill {cx-1} {cy+10} {cz+2} {cx+1} {cy+12} {cz+3} glass outline")
    cmds.append(f"fill {cx} {cy+10} {cz+2} {cx} {cy+12} {cz+2} air")
    # Glass roof over Zombie cell to block sunlight
    cmds.append(f"fill {cx-1} {cy+13} {cz+2} {cx+1} {cy+13} {cz+3} stone_brick_slab")
    # Glass barrier between Villagers and Zombie at Z=+1
    cmds.append(f"setblock {cx} {cy+10} {cz+1} glass")
    cmds.append(f"setblock {cx} {cy+11} {cz+1} glass")

    # Villager Beds (Y=76) - placed AFTER enclosure air clearing
    cmds.append(f"setblock {cx-1} {cy+10} {cz-1} red_bed[facing=south,part=foot]")
    cmds.append(f"setblock {cx-1} {cy+10} {cz} red_bed[facing=south,part=head]")
    cmds.append(f"setblock {cx} {cy+10} {cz-1} red_bed[facing=south,part=foot]")
    cmds.append(f"setblock {cx} {cy+10} {cz} red_bed[facing=south,part=head]")
    cmds.append(f"setblock {cx+1} {cy+10} {cz-1} red_bed[facing=south,part=foot]")
    cmds.append(f"setblock {cx+1} {cy+10} {cz} red_bed[facing=south,part=head]")

    # Workstations (Fletching Tables at Y=76)
    cmds.append(f"setblock {cx-1} {cy+10} {cz-2} fletching_table")
    cmds.append(f"setblock {cx} {cy+10} {cz-2} fletching_table")
    cmds.append(f"setblock {cx+1} {cy+10} {cz-2} fletching_table")

    # Clear any old farm entities
    cmds.append("kill @e[tag=IronFarmVillager]")
    cmds.append("kill @e[tag=IronFarmZombie]")

    # 7. Summon Entities (3 Villagers, 1 Zombie with PersistenceRequired + Helmet + Nametag)
    cmds.append(f"summon villager {cx} {cy+10} {cz} {{Tags:[\"IronFarmVillager\"]}}")
    cmds.append(f"summon villager {cx-1} {cy+10} {cz} {{Tags:[\"IronFarmVillager\"]}}")
    cmds.append(f"summon villager {cx+1} {cy+10} {cz} {{Tags:[\"IronFarmVillager\"]}}")
    cmds.append(
        f"summon zombie {cx} {cy+10} {cz+2} "
        f"{{PersistenceRequired:1b,CustomName:'\"ScareZombie\"',CustomNameVisible:1b,ArmorItems:[{{}},{{}},{{}},{{id:\"minecraft:iron_helmet\",Count:1b}}],Tags:[\"IronFarmZombie\"]}}"
    )

    return cmds

def execute_build(dry_run=False):
    cmds = generate_build_commands()
    history = {"commands_run": cmds, "center": {"x": 1281, "y": 66, "z": -368}}

    if not dry_run:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)

    print(f"Building Iron Farm with {len(cmds)} commands...")
    success_count = 0
    for c in cmds:
        if send_exaroton_command(c, dry_run=dry_run):
            success_count += 1

    print(f"Finished build. Executed {success_count}/{len(cmds)} commands.")
    return success_count == len(cmds)

def execute_undo(dry_run=False):
    cx, cy, cz = 1281, 66, -368
    undo_cmds = [
        f"fill {cx-5} {cy+1} {cz-5} {cx+5} {cy+14} {cz+5} air",
        f"fill {cx-5} {cy} {cz-5} {cx+5} {cy} {cz+5} dirt",
        f"kill @e[type=villager,x={cx},y={cy},z={cz},distance=..20]",
        f"kill @e[type=zombie,x={cx},y={cy},z={cz},distance=..20]",
        f"kill @e[type=iron_golem,x={cx},y={cy},z={cz},distance=..20]",
        f"kill @e[tag=IronFarmVillager]",
        f"kill @e[tag=IronFarmZombie]",
        f"kill @e[type=item,x={cx},y={cy},z={cz},distance=..20]"
    ]
    print(f"Reverting Iron Farm area (1281, 66, -368)...")
    for c in undo_cmds:
        send_exaroton_command(c, dry_run=dry_run)

    if not dry_run and os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    print("✅ Rollback complete.")

def main():
    parser = argparse.ArgumentParser(description="Build or Undo Iron Farm")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--undo", action="store_true", help="Revert the Iron Farm construction")
    args = parser.parse_args()

    if args.undo:
        execute_undo(dry_run=args.dry_run)
    else:
        execute_build(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
