#!/usr/bin/env python3
"""
Build a beautiful, authentic plains villager house strictly within the villager_house region bounds:
X: 1293 to 1300
Z: -230 to -222
Y Floor: 78 (Use base concrete floor as is)
Y Height: 79 to 92

Features:
- Corner oak log pillars
- Cobblestone foundation layer (Y=79)
- Oak wood plank upper walls (Y=80 to 83)
- Windows with glass panes
- West facing oak door
- Slanted A-frame oak stairs roof with overhangs and oak slab peak
- Cozy interior: 6 beds of different colors, lantern, crafting table, furnace, and bookshelves.

Supports --undo and --dry-run.
"""

import os
import sys
import json
import subprocess
import argparse

BACKUP_FILE = "WorldGuard/backups/villager_house_build_history.json"

ENV_FILE = ".env"
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
Y_FLOOR = 78 # Base floor to keep

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

def get_block_info(x, y, z):
    # WorldGuard / WorldEdit doesn't easily expose individual block queries via simple Exaroton console API,
    # so we'll just track the commands we run to build, and to undo we fill the region with air above Y_FLOOR.
    pass

def build_house(dry_run=False):
    print("=== Building Villager House ===")
    
    cmds = []
    
    # 0. Clear building height volume (Y=79 to 92)
    cmds.append(f"fill {MIN_X} 79 {MIN_Z} {MAX_X} 92 {MAX_Z} minecraft:air")
    
    # 1. Corner Oak Log Pillars (Y=79 to 83)
    for x in [MIN_X, MAX_X]:
        for z in [MIN_Z, MAX_Z]:
            cmds.append(f"fill {x} 79 {z} {x} 83 {z} minecraft:oak_log[axis=y]")
            
    # 2. Bottom Foundation Layer (Y=79) - Cobblestone (excluding corners)
    cmds.append(f"fill {MIN_X+1} 79 {MIN_Z} {MAX_X-1} 79 {MIN_Z} minecraft:cobblestone") # North wall
    cmds.append(f"fill {MIN_X+1} 79 {MAX_Z} {MAX_X-1} 79 {MAX_Z} minecraft:cobblestone") # South wall
    cmds.append(f"fill {MIN_X} 79 {MIN_Z+1} {MIN_X} 79 {MAX_Z-1} minecraft:cobblestone") # West wall
    cmds.append(f"fill {MAX_X} 79 {MIN_Z+1} {MAX_X} 79 {MAX_Z-1} minecraft:cobblestone") # East wall

    # 3. Upper Walls (Y=80 to 83) - Oak Planks (excluding corners)
    cmds.append(f"fill {MIN_X+1} 80 {MIN_Z} {MAX_X-1} 83 {MIN_Z} minecraft:oak_planks") # North wall
    cmds.append(f"fill {MIN_X+1} 80 {MAX_Z} {MAX_X-1} 83 {MAX_Z} minecraft:oak_planks") # South wall
    cmds.append(f"fill {MIN_X} 80 {MIN_Z+1} {MIN_X} 83 {MAX_Z-1} minecraft:oak_planks") # West wall
    cmds.append(f"fill {MAX_X} 80 {MIN_Z+1} {MAX_X} 83 {MAX_Z-1} minecraft:oak_planks") # East wall

    # 4. Windows (Y=81)
    cmds.append(f"setblock 1297 81 {MIN_Z} minecraft:glass_pane") # North window (single)
    cmds.append(f"setblock 1296 81 {MAX_Z} minecraft:glass_pane") # South window
    cmds.append(f"setblock 1297 81 {MAX_Z} minecraft:glass_pane") # South window
    cmds.append(f"setblock {MAX_X} 81 -226 minecraft:glass_pane") # East window

    # 5. Entrance Doors on WEST Wall (X=1293, Z=-226, Y=79..80) & NORTH Wall (X=1296, Z=-230, Y=79..80)
    cmds.append(f"setblock {MIN_X} 79 -226 minecraft:air")
    cmds.append(f"setblock {MIN_X} 80 -226 minecraft:air")
    cmds.append(f"setblock {MIN_X} 79 -226 minecraft:oak_door[half=lower,facing=west]")
    cmds.append(f"setblock {MIN_X} 80 -226 minecraft:oak_door[half=upper,facing=west]")

    cmds.append(f"setblock 1296 79 {MIN_Z} minecraft:air")
    cmds.append(f"setblock 1296 80 {MIN_Z} minecraft:air")
    cmds.append(f"setblock 1296 79 {MIN_Z} minecraft:oak_door[half=lower,facing=north]")
    cmds.append(f"setblock 1296 80 {MIN_Z} minecraft:oak_door[half=upper,facing=north]")
    cmds.append(f"setblock 1296 81 {MIN_Z} minecraft:oak_planks")
    
    # 6. Flat Ceiling (Y=84)
    cmds.append(f"fill {MIN_X+1} 84 {MIN_Z+1} {MAX_X-1} 84 {MAX_Z-1} minecraft:oak_planks")
    
    # 7. Roof Gable Ends (Trusses at X=MIN_X and MAX_X)
    for x in [MIN_X, MAX_X]:
        cmds.append(f"fill {x} 84 {MIN_Z+1} {x} 84 {MAX_Z-1} minecraft:oak_planks")
        cmds.append(f"fill {x} 85 {MIN_Z+2} {x} 85 {MAX_Z-2} minecraft:oak_planks")
        cmds.append(f"fill {x} 86 {MIN_Z+3} {x} 86 {MAX_Z-3} minecraft:oak_planks")
        cmds.append(f"fill {x} 87 {MIN_Z+4} {x} 87 {MAX_Z-4} minecraft:oak_planks")

    # 8. Slanted Roof Stairs (Y=84 to 87)
    # Y=84
    cmds.append(f"fill {MIN_X} 84 {MIN_Z} {MAX_X} 84 {MIN_Z} minecraft:oak_stairs[facing=south]")
    cmds.append(f"fill {MIN_X} 84 {MAX_Z} {MAX_X} 84 {MAX_Z} minecraft:oak_stairs[facing=north]")
    # Y=85
    cmds.append(f"fill {MIN_X} 85 {MIN_Z+1} {MAX_X} 85 {MIN_Z+1} minecraft:oak_stairs[facing=south]")
    cmds.append(f"fill {MIN_X} 85 {MAX_Z-1} {MAX_X} 85 {MAX_Z-1} minecraft:oak_stairs[facing=north]")
    # Y=86
    cmds.append(f"fill {MIN_X} 86 {MIN_Z+2} {MAX_X} 86 {MIN_Z+2} minecraft:oak_stairs[facing=south]")
    cmds.append(f"fill {MIN_X} 86 {MAX_Z-2} {MAX_X} 86 {MAX_Z-2} minecraft:oak_stairs[facing=north]")
    # Y=87
    cmds.append(f"fill {MIN_X} 87 {MIN_Z+3} {MAX_X} 87 {MIN_Z+3} minecraft:oak_stairs[facing=south]")
    cmds.append(f"fill {MIN_X} 87 {MAX_Z-3} {MAX_X} 87 {MAX_Z-3} minecraft:oak_stairs[facing=north]")
    
    # Y=88 (Roof peak slab)
    cmds.append(f"fill {MIN_X} 88 -226 {MAX_X} 88 -226 minecraft:oak_slab[type=bottom]")

    # 9. Cozy Interior Elements (Y=79)
    # Hanging lanterns
    cmds.append(f"setblock 1295 83 -226 minecraft:lantern[hanging=true]")
    cmds.append(f"setblock 1298 83 -226 minecraft:lantern[hanging=true]")

    # Furniture
    cmds.append(f"setblock 1299 79 -223 minecraft:crafting_table")
    cmds.append(f"setblock 1299 79 -224 minecraft:furnace")
    cmds.append(f"setblock 1299 79 -228 minecraft:bookshelf")
    cmds.append(f"setblock 1299 79 -229 minecraft:bookshelf")

    # 6 Villager Job Site Items
    cmds.append(f"setblock 1299 79 -225 minecraft:composter")
    cmds.append(f"setblock 1299 79 -226 minecraft:lectern[facing=west]")
    cmds.append(f"setblock 1299 79 -227 minecraft:stonecutter")
    cmds.append(f"setblock 1298 79 -223 minecraft:cartography_table")
    cmds.append(f"setblock 1298 79 -224 minecraft:fletching_table")
    cmds.append(f"setblock 1298 79 -229 minecraft:grindstone[facing=west]")

    # Beds for Villagers
    # Bed 1 (Red bed, facing North)
    cmds.append(f"setblock 1294 79 -223 minecraft:red_bed[part=foot,facing=north]")
    cmds.append(f"setblock 1294 79 -224 minecraft:red_bed[part=head,facing=north]")
    # Bed 2 (Yellow bed, facing North)
    cmds.append(f"setblock 1295 79 -223 minecraft:yellow_bed[part=foot,facing=north]")
    cmds.append(f"setblock 1295 79 -224 minecraft:yellow_bed[part=head,facing=north]")
    # Bed 3 (Lime bed, facing North)
    cmds.append(f"setblock 1296 79 -223 minecraft:lime_bed[part=foot,facing=north]")
    cmds.append(f"setblock 1296 79 -224 minecraft:lime_bed[part=head,facing=north]")
    # Bed 4 (Blue bed, facing South)
    cmds.append(f"setblock 1294 79 -229 minecraft:blue_bed[part=foot,facing=south]")
    cmds.append(f"setblock 1294 79 -228 minecraft:blue_bed[part=head,facing=south]")
    # Bed 5 (Cyan bed, facing South)
    cmds.append(f"setblock 1295 79 -229 minecraft:cyan_bed[part=foot,facing=south]")
    cmds.append(f"setblock 1295 79 -228 minecraft:cyan_bed[part=head,facing=south]")
    # Bed 6 (Purple bed, facing South)
    cmds.append(f"setblock 1296 79 -229 minecraft:purple_bed[part=foot,facing=south]")
    cmds.append(f"setblock 1296 79 -228 minecraft:purple_bed[part=head,facing=south]")

    if dry_run:
        print(f"[DRY-RUN] Would execute {len(cmds)} commands to build the house.")
        for cmd in cmds[:5]:
            print(f"  {cmd}")
        print("  ...")
        return True

    # Execute commands
    import concurrent.futures
    
    # 1. Clear volume first (must be synchronous)
    print("Clearing building volume...")
    send_exaroton_command(cmds[0])
    
    # 2. Run the rest of the commands in parallel
    print(f"Running {len(cmds)-1} building commands in parallel...")
    success_count = 1  # For the first clear command
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Map the commands to exaroton executor
        results = executor.map(send_exaroton_command, cmds[1:])
        for res in results:
            if res:
                success_count += 1
                
    # 3. Clean up dropped loot in/near the house
    loot_cmd = "kill @e[type=item,x=1296,y=79,z=-226,distance=..30]"
    print("Cleaning up dropped items/loot...")
    if send_exaroton_command(loot_cmd):
        print("Dropped loot cleared successfully.")
            
    print(f"Executed {success_count}/{len(cmds)} commands successfully on the server.")
    
    # Save backup history
    history = {
        "status": "built",
        "min_x": MIN_X,
        "max_x": MAX_X,
        "min_z": MIN_Z,
        "max_z": MAX_Z,
        "y_start": 79,
        "y_end": 92
    }
    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    with open(BACKUP_FILE, "w") as f:
        json.dump(history, f, indent=4)
        
    print(f"Saved build history to {BACKUP_FILE}.")
    return True

def undo(dry_run=False):
    if dry_run:
        print(f"[DRY-RUN] Would fill Y=79 to 92 with air to undo building.")
        return True

    print("=== Reverting Villager House Building ===")
    cmd = f"fill {MIN_X} 79 {MIN_Z} {MAX_X} 92 {MAX_Z} minecraft:air"
    if send_exaroton_command(cmd):
        print(f"Successfully cleared Y=79 to 92 using command: {cmd}")
        if os.path.exists(BACKUP_FILE):
            os.remove(BACKUP_FILE)
            print("Removed build history file.")
        return True
    else:
        print("[ERROR] Undo command failed.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Build/revert villager house in region bounds.")
    parser.add_argument("--dry-run", action="store_true", help="Preview commands without sending.")
    parser.add_argument("--undo", action="store_true", help="Revert the house back to air.")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        build_house(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
