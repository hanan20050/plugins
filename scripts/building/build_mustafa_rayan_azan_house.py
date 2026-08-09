#!/usr/bin/env python3
"""
Mustafa, Rayan, and Azan Joint House Builder
--------------------------------------------
Constructs a premium 2-story house with custom roof, interior design,
furnishings, and full height calculation in region `mustafa_azan_rayan`
at X: 1292..1299, Z: -230..-222, Y: 78..90.

Usage:
  python3 build_mustafa_rayan_azan_house.py [--dry-run]
  python3 build_mustafa_rayan_azan_house.py --undo [--dry-run]
"""

import os
import sys
import json
import subprocess
import argparse

# Credentials and constants
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
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "mustafa_rayan_azan_house_history.json")

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
        if data.get("success"):
            print(f"✅ Executed: {cmd}")
            return True
        else:
            print(f"❌ Error executing '{cmd}': {data.get('error')}")
            return False
    except Exception:
        print(f"Response for '{cmd}': {res.stdout}")
        return False

def generate_house_commands():
    min_x, max_x = 1292, 1299
    min_z, max_z = -230, -222
    base_y = 78

    cmds = []

    # 1. Clear area (Y=78 to 92)
    cmds.append(f"fill {min_x-2} {base_y} {min_z-2} {max_x+2} {base_y+14} {max_z+2} air")

    # 2. Base Floor (Y=78)
    cmds.append(f"fill {min_x} {base_y} {min_z} {max_x} {base_y} {max_z} spruce_planks")
    cmds.append(f"fill {min_x} {base_y} {min_z} {max_x} {base_y} {min_z} cobblestone")
    cmds.append(f"fill {min_x} {base_y} {max_z} {max_x} {base_y} {max_z} cobblestone")
    cmds.append(f"fill {min_x} {base_y} {min_z} {min_x} {base_y} {max_z} cobblestone")
    cmds.append(f"fill {max_x} {base_y} {min_z} {max_x} {base_y} {max_z} cobblestone")

    # 3. Corner Pillars (Oak Logs Y=79 to 86)
    cmds.append(f"fill {min_x} {base_y+1} {min_z} {min_x} {base_y+8} {min_z} oak_log")
    cmds.append(f"fill {max_x} {base_y+1} {min_z} {max_x} {base_y+8} {min_z} oak_log")
    cmds.append(f"fill {min_x} {base_y+1} {max_z} {min_x} {base_y+8} {max_z} oak_log")
    cmds.append(f"fill {max_x} {base_y+1} {max_z} {max_x} {base_y+8} {max_z} oak_log")

    # 4. Ground Floor Walls (Y=79 to 82)
    # Bottom stone bricks Y=79
    cmds.append(f"fill {min_x+1} {base_y+1} {min_z} {max_x-1} {base_y+1} {min_z} stone_bricks")
    cmds.append(f"fill {min_x+1} {base_y+1} {max_z} {max_x-1} {base_y+1} {max_z} stone_bricks")
    cmds.append(f"fill {min_x} {base_y+1} {min_z+1} {min_x} {base_y+1} {max_z-1} stone_bricks")
    cmds.append(f"fill {max_x} {base_y+1} {min_z+1} {max_x} {base_y+1} {max_z-1} stone_bricks")

    # Wall planks Y=80..82
    cmds.append(f"fill {min_x+1} {base_y+2} {min_z} {max_x-1} {base_y+4} {min_z} oak_planks")
    cmds.append(f"fill {min_x+1} {base_y+2} {max_z} {max_x-1} {base_y+4} {max_z} oak_planks")
    cmds.append(f"fill {min_x} {base_y+2} {min_z+1} {min_x} {base_y+4} {max_z-1} oak_planks")
    cmds.append(f"fill {max_x} {base_y+2} {min_z+1} {max_x} {base_y+4} {max_z-1} oak_planks")

    # Ground floor windows (Glass Panes Y=80..81)
    cmds.append(f"fill {1295} {base_y+2} {min_z} {1296} {base_y+3} {min_z} glass_pane")
    cmds.append(f"fill {min_x} {base_y+2} {-227} {min_x} {base_y+3} {-225} glass_pane")
    cmds.append(f"fill {max_x} {base_y+2} {-227} {max_x} {base_y+3} {-225} glass_pane")

    # Front Door (South side center X=1295, Z=-222)
    cmds.append(f"fill {1295} {base_y+1} {max_z} {1295} {base_y+2} {max_z} air")
    cmds.append(f"setblock {1295} {base_y+1} {max_z} oak_door[half=lower,facing=south]")
    cmds.append(f"setblock {1295} {base_y+2} {max_z} oak_door[half=upper,facing=south]")

    # 5. Second Floor Ceiling/Floor (Y=83) & Ladder
    cmds.append(f"fill {min_x+1} {base_y+5} {min_z+1} {max_x-1} {base_y+5} {max_z-1} spruce_planks")
    cmds.append(f"setblock {1293} {base_y+5} {-223} air")
    cmds.append(f"fill {1293} {base_y+1} {-223} {1293} {base_y+4} {-223} ladder[facing=east]")

    # 6. Upper Floor Walls (Y=84 to 86)
    cmds.append(f"fill {min_x+1} {base_y+6} {min_z} {max_x-1} {base_y+8} {min_z} oak_planks")
    cmds.append(f"fill {min_x+1} {base_y+6} {max_z} {max_x-1} {base_y+8} {max_z} oak_planks")
    cmds.append(f"fill {min_x} {base_y+6} {min_z+1} {min_x} {base_y+8} {max_z-1} oak_planks")
    cmds.append(f"fill {max_x} {base_y+6} {min_z+1} {max_x} {base_y+8} {max_z-1} oak_planks")

    # Upper floor windows (Y=85)
    cmds.append(f"fill {1295} {base_y+7} {min_z} {1296} {base_y+7} {min_z} glass_pane")
    cmds.append(f"fill {min_x} {base_y+7} {-227} {min_x} {base_y+7} {-225} glass_pane")
    cmds.append(f"fill {max_x} {base_y+7} {-227} {max_x} {base_y+7} {-225} glass_pane")

    # 7. Interior Furnishings (Upper floor Y=84)
    # Mustafa Bed (Red)
    cmds.append(f"setblock {1293} {base_y+6} {-230} red_bed[facing=south,part=head]")
    cmds.append(f"setblock {1293} {base_y+6} {-229} red_bed[facing=south,part=foot]")

    # Rayan Bed (Blue)
    cmds.append(f"setblock {1296} {base_y+6} {-230} blue_bed[facing=south,part=head]")
    cmds.append(f"setblock {1296} {base_y+6} {-229} blue_bed[facing=south,part=foot]")

    # Azan Bed (Yellow)
    cmds.append(f"setblock {1298} {base_y+6} {-230} yellow_bed[facing=south,part=head]")
    cmds.append(f"setblock {1298} {base_y+6} {-229} yellow_bed[facing=south,part=foot]")

    # Utilities & Storage
    cmds.append(f"setblock {1297} {base_y+6} {-223} chest[facing=north,type=left]")
    cmds.append(f"setblock {1298} {base_y+6} {-223} chest[facing=north,type=right]")
    cmds.append(f"setblock {1296} {base_y+6} {-223} crafting_table")
    cmds.append(f"setblock {1295} {base_y+6} {-223} anvil")

    # Lighting
    cmds.append(f"setblock {1296} {base_y+4} {-226} lantern[hanging=true]")
    cmds.append(f"setblock {1296} {base_y+8} {-226} lantern[hanging=true]")

    # 8. Gabled Roof (Y=87 to 90)
    # Roof Trim & Slopes along X axis
    # Y=87 (Roof Base)
    cmds.append(f"fill {1291} {base_y+9} {min_z-1} {1291} {base_y+9} {max_z+1} stone_brick_stairs[facing=east]")
    cmds.append(f"fill {1300} {base_y+9} {min_z-1} {1300} {base_y+9} {max_z+1} stone_brick_stairs[facing=west]")
    cmds.append(f"fill {1292} {base_y+9} {min_z-1} {1292} {base_y+9} {max_z+1} spruce_stairs[facing=east]")
    cmds.append(f"fill {1299} {base_y+9} {min_z-1} {1299} {base_y+9} {max_z+1} spruce_stairs[facing=west]")

    # Y=88
    cmds.append(f"fill {1292} {base_y+10} {min_z-1} {1292} {base_y+10} {max_z+1} stone_brick_stairs[facing=east]")
    cmds.append(f"fill {1299} {base_y+10} {min_z-1} {1299} {base_y+10} {max_z+1} stone_brick_stairs[facing=west]")
    cmds.append(f"fill {1293} {base_y+10} {min_z-1} {1293} {base_y+10} {max_z+1} spruce_stairs[facing=east]")
    cmds.append(f"fill {1298} {base_y+10} {min_z-1} {1298} {base_y+10} {max_z+1} spruce_stairs[facing=west]")

    # Y=89
    cmds.append(f"fill {1293} {base_y+11} {min_z-1} {1293} {base_y+11} {max_z+1} stone_brick_stairs[facing=east]")
    cmds.append(f"fill {1298} {base_y+11} {min_z-1} {1298} {base_y+11} {max_z+1} stone_brick_stairs[facing=west]")
    cmds.append(f"fill {1294} {base_y+11} {min_z-1} {1294} {base_y+11} {max_z+1} spruce_stairs[facing=east]")
    cmds.append(f"fill {1297} {base_y+11} {min_z-1} {1297} {base_y+11} {max_z+1} spruce_stairs[facing=west]")

    # Y=90 (Roof Ridge Peak)
    cmds.append(f"fill {1294} {base_y+12} {min_z-1} {1294} {base_y+12} {max_z+1} stone_brick_slab[type=bottom]")
    cmds.append(f"fill {1297} {base_y+12} {min_z-1} {1297} {base_y+12} {max_z+1} stone_brick_slab[type=bottom]")
    cmds.append(f"fill {1295} {base_y+12} {min_z-1} {1296} {base_y+12} {max_z+1} spruce_slab[type=bottom]")

    # Gable End Walls (Under Roof Slopes)
    cmds.append(f"fill {1293} {base_y+9} {min_z} {1298} {base_y+9} {min_z} oak_planks")
    cmds.append(f"fill {1293} {base_y+9} {max_z} {1298} {base_y+9} {max_z} oak_planks")
    cmds.append(f"fill {1294} {base_y+10} {min_z} {1297} {base_y+10} {min_z} oak_planks")
    cmds.append(f"fill {1294} {base_y+10} {max_z} {1297} {base_y+10} {max_z} oak_planks")
    cmds.append(f"fill {1295} {base_y+11} {min_z} {1296} {base_y+11} {min_z} oak_planks")
    cmds.append(f"fill {1295} {base_y+11} {max_z} {1296} {base_y+11} {max_z} oak_planks")

    return cmds

def main():
    parser = argparse.ArgumentParser(description="Mustafa, Rayan, and Azan House Builder")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--undo", action="store_true", help="Undo construction by clearing house area")
    args = parser.parse_args()

    min_x, max_x = 1292, 1299
    min_z, max_z = -230, -222
    base_y = 78

    if args.undo:
        print("🔄 Undoing Mustafa, Rayan, and Azan House construction...")
        clear_cmd = f"fill {min_x-3} {base_y} {min_z-3} {max_x+3} {base_y+15} {max_z+3} air"
        success = send_exaroton_command(clear_cmd, dry_run=args.dry_run)
        if success and os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
            print("✨ History cleared and house removed successfully.")
        return

    commands = generate_house_commands()
    print(f"🏠 Building 2-Story House for Mustafa, Rayan & Azan at (X: 1292..1299, Z: -230..-222, Y: 78..90)... Total steps: {len(commands)}")

    history = {
        "region": "mustafa_azan_rayan",
        "bounds": [min_x, base_y, min_z, max_x, base_y+14, max_z],
        "commands": commands
    }

    executed_count = 0
    for cmd in commands:
        if send_exaroton_command(cmd, dry_run=args.dry_run):
            executed_count += 1

    if not args.dry_run:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)

    print(f"🎉 House construction finished! ({executed_count}/{len(commands)} steps executed successfully)")

if __name__ == "__main__":
    main()
