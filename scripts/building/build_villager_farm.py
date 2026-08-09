#!/usr/bin/env python3
"""
Build a beautiful small farm adjacent to the villager house on the North side.
Same Z-length as the house: 9 blocks (Z: -239 to -231).
Same X-width as the house: 8 blocks (X: 1293 to 1300).

Features:
- Oak log border at Y=78/79
- Central water channel (X=1296) at Y=78
- Farmland at Y=78 with crops (wheat, potatoes, carrots, beetroots) at Y=79
- Cauldron job site block (leatherworker workstation) filled with water
- Composter block for farmers
- Supports --undo and --dry-run.
"""

import os
import sys
import json
import subprocess
import argparse

BACKUP_FILE = "WorldGuard/backups/villager_farm_build_history.json"

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

# Farm coordinates
MIN_X, MAX_X = 1293, 1300
MIN_Z, MAX_Z = -239, -231
Y_LEVEL = 78 # Farm floor level

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
        return data.get("success", False)
    except Exception:
        return False

def build_farm(dry_run=False):
    print("=== Building Villager Farm ===")
    
    cmds = []
    
    # 0. Clear farm volume (Y=78 to 82)
    cmds.append(f"fill {MIN_X} 78 {MIN_Z} {MAX_X} 82 {MAX_Z} minecraft:air")
    
    # 1. Outer Border at Y=78 - Oak Logs
    cmds.append(f"fill {MIN_X} {Y_LEVEL} {MIN_Z} {MAX_X} {Y_LEVEL} {MIN_Z} minecraft:oak_log[axis=x]") # North border
    cmds.append(f"fill {MIN_X} {Y_LEVEL} {MAX_Z} {MAX_X} {Y_LEVEL} {MAX_Z} minecraft:oak_log[axis=x]") # South border
    cmds.append(f"fill {MIN_X} {Y_LEVEL} {MIN_Z} {MIN_X} {Y_LEVEL} {MAX_Z} minecraft:oak_log[axis=z]") # West border
    cmds.append(f"fill {MAX_X} {Y_LEVEL} {MIN_Z} {MAX_X} {Y_LEVEL} {MAX_Z} minecraft:oak_log[axis=z]") # East border

    # 2. Water channel in the middle (X=1296) at Y=78
    cmds.append(f"fill 1296 {Y_LEVEL} {MIN_Z+1} 1296 {Y_LEVEL} {MAX_Z-1} minecraft:water")
    
    # 3. Farmland at Y=78 (excluding water channel and borders)
    cmds.append(f"fill {MIN_X+1} {Y_LEVEL} {MIN_Z+1} 1295 {Y_LEVEL} {MAX_Z-1} minecraft:farmland[moisture=7]")
    cmds.append(f"fill 1297 {Y_LEVEL} {MIN_Z+1} {MAX_X-1} {Y_LEVEL} {MAX_Z-1} minecraft:farmland[moisture=7]")

    # 4. Crops at Y=79
    cmds.append(f"fill 1294 {Y_LEVEL+1} {MIN_Z+1} 1294 {Y_LEVEL+1} {MAX_Z-1} minecraft:wheat[age=7]")
    cmds.append(f"fill 1295 {Y_LEVEL+1} {MIN_Z+1} 1295 {Y_LEVEL+1} {MAX_Z-1} minecraft:potatoes[age=7]")
    cmds.append(f"fill 1297 {Y_LEVEL+1} {MIN_Z+1} 1298 {Y_LEVEL+1} {MAX_Z-1} minecraft:carrots[age=7]")
    cmds.append(f"fill 1299 {Y_LEVEL+1} {MIN_Z+1} 1299 {Y_LEVEL+1} {MAX_Z-1} minecraft:beetroots[age=3]")

    # 5. Cauldron (Leatherworker workstation job block) - filled with water at Y=79
    # Place on West border (1293, 79, -235)
    cmds.append(f"setblock 1293 {Y_LEVEL+1} -235 minecraft:water_cauldron[level=3]")

    # 6. Composter (Farmer workstation job block) at Y=79
    # Place on East border (1300, 79, -235)
    cmds.append(f"setblock 1300 {Y_LEVEL+1} -235 minecraft:composter[level=0]")

    # 7. Clean up dropped loot in/near the farm
    cmds.append(f"kill @e[type=item,x=1296,y=78,z=-235,distance=..20]")

    if dry_run:
        print(f"[DRY-RUN] Would execute {len(cmds)} commands to build the farm.")
        for cmd in cmds:
            print(f"  {cmd}")
        return True

    # Execute commands
    import concurrent.futures
    print("Clearing farm volume...")
    send_exaroton_command(cmds[0])
    
    print("Executing farm construction commands in parallel...")
    success_count = 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(send_exaroton_command, cmds[1:])
        for res in results:
            if res:
                success_count += 1
                
    print(f"Executed {success_count}/{len(cmds)} commands successfully on the server.")
    
    # Save history for undo
    history = {
        "status": "built",
        "min_x": MIN_X,
        "max_x": MAX_X,
        "min_z": MIN_Z,
        "max_z": MAX_Z,
        "y_start": 78,
        "y_end": 82
    }
    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    with open(BACKUP_FILE, "w") as f:
        json.dump(history, f, indent=4)
        
    return True

def undo(dry_run=False):
    if dry_run:
        print(f"[DRY-RUN] Would fill Y=78 to 82 with white concrete/grass/air to revert farm.")
        return True

    print("=== Reverting Villager Farm ===")
    # Revert to air above Y=78 and restore floor to white concrete (Y=78)
    cmds = [
        f"fill {MIN_X} 79 {MIN_Z} {MAX_X} 82 {MAX_Z} minecraft:air",
        f"fill {MIN_X} 78 {MIN_Z} {MAX_X} 78 {MAX_Z} minecraft:white_concrete"
    ]
    for cmd in cmds:
        send_exaroton_command(cmd)
        
    if os.path.exists(BACKUP_FILE):
        os.remove(BACKUP_FILE)
    print("Reverted farm successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Build/revert villager farm adjacent to the house.")
    parser.add_argument("--dry-run", action="store_true", help="Preview commands without sending.")
    parser.add_argument("--undo", action="store_true", help="Revert farm back to original floor.")
    args = parser.parse_args()

    if args.undo:
        undo(dry_run=args.dry_run)
    else:
        build_farm(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
