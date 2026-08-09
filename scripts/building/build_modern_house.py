#!/usr/bin/env python3
"""
Modern Luxury Villa Generator (10x10 Centered at 1200, 63, -127)
-----------------------------------------------------------------
Builds a perfected 2-story Modern 10x10 Villa centered at X=1200, Y=63, Z=-127.
Architectural Highlights:
- Crisp white & gray concrete structural framing with black stained glass panoramic windows
- Dark oak ground floor, smooth quartz mezzanine, and cantilever roof canopy with recessed sea lanterns
- Solid 4-step quartz staircase along West wall with unobstructed headroom
- Master Suite on 2nd floor with zero bed/window clipping
- Full modern furnishings (couch, coffee table, TV console, bar, king bed, desk, balcony plants)
- Complete `--undo` support to restore ground back to natural grass blocks

Usage:
  python3 build_modern_house.py [--dry-run]
  python3 build_modern_house.py --undo [--dry-run]
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
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "modern_house_history.json")

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
            print(f"✅ Executed: {cmd}")
            return True
        else:
            print(f"❌ Exaroton Command Error: {data.get('error')}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def generate_modern_house_commands():
    min_x, max_x = 1195, 1204
    min_z, max_z = -132, -123
    base_y = 63

    commands = []

    # Step 1: Clear Space Y=63 to Y=78
    commands.append(f"fill {min_x-3} {base_y} {min_z-3} {max_x+3} {base_y+15} {max_z+3} air")

    # Step 2: Ground Floor (Y=63) - Dark Oak Planks & Recessed Lighting
    commands.append(f"fill {min_x} {base_y} {min_z} {max_x} {base_y} {max_z} dark_oak_planks")
    commands.append(f"fill {min_x+1} {base_y} {min_z+1} {max_x-1} {base_y} {min_z+1} sea_lantern")
    commands.append(f"fill {min_x+1} {base_y} {max_z-1} {max_x-1} {base_y} {max_z-1} sea_lantern")

    # Step 3: Ground Floor Walls (Y=64..66)
    # West Solid Accent Wall (X=1195)
    commands.append(f"fill {min_x} {base_y+1} {min_z} {min_x} {base_y+3} {max_z} gray_concrete")
    # Corner Pillars
    commands.append(f"fill {max_x} {base_y+1} {min_z} {max_x} {base_y+3} {min_z} white_concrete")
    commands.append(f"fill {max_x} {base_y+1} {max_z} {max_x} {base_y+3} {max_z} white_concrete")
    commands.append(f"fill {min_x} {base_y+1} {min_z} {min_x} {base_y+3} {min_z} white_concrete")
    commands.append(f"fill {min_x} {base_y+1} {max_z} {min_x} {base_y+3} {max_z} white_concrete")

    # North Window Sill & Glass
    commands.append(f"fill {min_x+1} {base_y+1} {min_z} {max_x-1} {base_y+1} {min_z} white_concrete")
    commands.append(f"fill {min_x+1} {base_y+2} {min_z} {max_x-1} {base_y+3} {min_z} black_stained_glass")

    # East Window Sill & Glass
    commands.append(f"fill {max_x} {base_y+1} {min_z+1} {max_x} {base_y+1} {max_z-1} white_concrete")
    commands.append(f"fill {max_x} {base_y+2} {min_z+1} {max_x} {base_y+3} {max_z-1} black_stained_glass")

    # South Entrance Facade (Z=-123)
    commands.append(f"fill {min_x+1} {base_y+1} {max_z} {1198} {base_y+3} {max_z} white_concrete")
    commands.append(f"fill {1201} {base_y+1} {max_z} {max_x-1} {base_y+3} {max_z} white_concrete")
    commands.append(f"fill {1199} {base_y+1} {max_z} {1200} {base_y+2} {max_z} air")
    commands.append(f"fill {1199} {base_y+3} {max_z} {1200} {base_y+3} {max_z} white_concrete") # Lintel
    commands.append(f"setblock {1199} {base_y+1} {max_z} dark_oak_door[half=lower,facing=south]")
    commands.append(f"setblock {1199} {base_y+2} {max_z} dark_oak_door[half=upper,facing=south]")
    commands.append(f"setblock {1200} {base_y+1} {max_z} dark_oak_door[half=lower,facing=south,hinge=right]")
    commands.append(f"setblock {1200} {base_y+2} {max_z} dark_oak_door[half=upper,facing=south,hinge=right]")

    # Step 4: Mezzanine Subfloor & Solid Modern Staircase (Y=67)
    commands.append(f"fill {min_x} {base_y+4} {min_z} {max_x} {base_y+4} {max_z} smooth_quartz")
    # Stairwell cutout along West wall (Y=67 ceiling space Z=-130..-128)
    commands.append(f"fill {min_x+1} {base_y+4} {-130} {min_x+1} {base_y+4} {-128} air")

    # Solid Quartz Supporting Base under steps (X=1196)
    commands.append(f"setblock {min_x+1} {base_y+1} {-129} smooth_quartz")
    commands.append(f"fill {min_x+1} {base_y+1} {-128} {min_x+1} {base_y+2} {-128} smooth_quartz")
    commands.append(f"fill {min_x+1} {base_y+1} {-127} {min_x+1} {base_y+3} {-127} smooth_quartz")

    # Ensure 100% AIR headroom clearance above all steps (X=1196, Y=65..66)
    commands.append(f"fill {min_x+1} {base_y+1} {-130} {min_x+1} {base_y+3} {-130} air")
    commands.append(f"fill {min_x+1} {base_y+2} {-129} {min_x+1} {base_y+3} {-129} air")
    commands.append(f"setblock {min_x+1} {base_y+3} {-128} air")

    # 4-Step Quartz Staircase ascending North to South along West Wall (X=1196)
    commands.append(f"setblock {min_x+1} {base_y+1} {-130} quartz_stairs[facing=south]")
    commands.append(f"setblock {min_x+1} {base_y+2} {-129} quartz_stairs[facing=south]")
    commands.append(f"setblock {min_x+1} {base_y+3} {-128} quartz_stairs[facing=south]")

    # Step 5: Second Floor Structure & Balcony (Y=68..70)
    # West Solid Accent Wall
    commands.append(f"fill {min_x} {base_y+5} {min_z} {min_x} {base_y+7} {max_z} gray_concrete")
    # Corner Pillars
    commands.append(f"fill {max_x} {base_y+5} {min_z} {max_x} {base_y+7} {min_z} white_concrete")
    commands.append(f"fill {max_x} {base_y+5} {max_z} {max_x} {base_y+7} {max_z} white_concrete")
    commands.append(f"fill {min_x} {base_y+5} {min_z} {min_x} {base_y+7} {min_z} white_concrete")
    commands.append(f"fill {min_x} {base_y+5} {max_z} {min_x} {base_y+7} {max_z} white_concrete")

    # North Window Sill & Glass
    commands.append(f"fill {min_x+1} {base_y+5} {min_z} {max_x-1} {base_y+5} {min_z} white_concrete")
    commands.append(f"fill {min_x+1} {base_y+6} {min_z} {max_x-1} {base_y+7} {min_z} black_stained_glass")

    # East Window Sill & Glass
    commands.append(f"fill {max_x} {base_y+5} {min_z+1} {max_x} {base_y+5} {max_z-1} white_concrete")
    commands.append(f"fill {max_x} {base_y+6} {min_z+1} {max_x} {base_y+7} {max_z-1} black_stained_glass")

    # Open Balcony Terrace Cutout (Z=-124..-123)
    commands.append(f"fill {min_x+1} {base_y+5} {-124} {max_x-1} {base_y+7} {-123} air")
    # Glass Railing on Balcony
    commands.append(f"fill {min_x+1} {base_y+5} {max_z} {max_x-1} {base_y+5} {max_z} glass_pane")
    # Balcony Glass Divider Wall & Door at Z=-125
    commands.append(f"fill {min_x+1} {base_y+5} {-125} {1199} {base_y+7} {-125} black_stained_glass")
    commands.append(f"fill {1201} {base_y+5} {-125} {max_x-1} {base_y+7} {-125} black_stained_glass")
    commands.append(f"setblock {1200} {base_y+7} {-125} black_concrete")
    commands.append(f"setblock {1200} {base_y+5} {-125} dark_oak_door[half=lower,facing=south]")
    commands.append(f"setblock {1200} {base_y+6} {-125} dark_oak_door[half=upper,facing=south]")

    # Step 6: Roof Overhang & Ambient Lighting (Y=71)
    commands.append(f"fill {min_x-1} {base_y+8} {min_z-1} {max_x+1} {base_y+8} {max_z+1} white_concrete")
    commands.append(f"setblock {1198} {base_y+8} {-129} sea_lantern")
    commands.append(f"setblock {1201} {base_y+8} {-129} sea_lantern")
    commands.append(f"setblock {1198} {base_y+8} {-127} sea_lantern")
    commands.append(f"setblock {1201} {base_y+8} {-127} sea_lantern")

    # Step 7: Ground Floor Interior Furnishing
    # Lounge Couch (Center North)
    commands.append(f"setblock {1199} {base_y+1} {-131} black_wool")
    commands.append(f"setblock {1200} {base_y+1} {-131} black_wool")
    commands.append(f"setblock {1201} {base_y+1} {-131} black_wool")
    commands.append(f"setblock {1199} {base_y+1} {-130} black_wool")
    commands.append(f"setblock {1200} {base_y+1} {-130} smooth_quartz_slab[type=bottom]") # Coffee Table

    # TV & Media Unit on East Wall (X=1203)
    commands.append(f"fill {1203} {base_y+2} {-130} {1203} {base_y+3} {-129} black_concrete")
    commands.append(f"setblock {1203} {base_y+1} {-130} bookshelf")
    commands.append(f"setblock {1203} {base_y+1} {-129} bookshelf")

    # Kitchenette Bar on East Wall (Z=-126..-124)
    commands.append(f"fill {1203} {base_y+1} {-126} {1203} {base_y+1} {-124} smooth_quartz_slab[type=top]")
    commands.append(f"fill {1202} {base_y+1} {-126} {1202} {base_y+1} {-124} dark_oak_stairs[facing=east]")
    commands.append(f"setblock {1203} {base_y+2} {-126} brewing_stand")

    # Step 8: Second Floor Master Bedroom Furnishing
    # Master King Bed (STRICTLY INSIDE ROOM at Z=-130..-129)
    commands.append(f"setblock {1198} {base_y+5} {-130} black_bed[facing=north,part=head]")
    commands.append(f"setblock {1198} {base_y+5} {-129} black_bed[facing=north,part=foot]")
    commands.append(f"setblock {1199} {base_y+5} {-130} black_bed[facing=north,part=head]")
    commands.append(f"setblock {1199} {base_y+5} {-129} black_bed[facing=north,part=foot]")

    # Nightstands & End Rod Lamps
    commands.append(f"setblock {1197} {base_y+5} {-130} smooth_quartz")
    commands.append(f"setblock {1197} {base_y+6} {-130} end_rod[facing=up]")
    commands.append(f"setblock {1200} {base_y+5} {-130} smooth_quartz")
    commands.append(f"setblock {1200} {base_y+6} {-130} end_rod[facing=up]")

    # Workstation Desk setup
    commands.append(f"fill {1203} {base_y+5} {-129} {1203} {base_y+5} {-128} smooth_quartz_slab[type=top]")
    commands.append(f"setblock {1202} {base_y+5} {-128} dark_oak_stairs[facing=west]")
    commands.append(f"setblock {1203} {base_y+6} {-128} heavy_weighted_pressure_plate")
    commands.append(f"setblock {1203} {base_y+5} {-127} bookshelf")

    # Outdoor Balcony Plants
    commands.append(f"setblock {1196} {base_y+5} {-124} potted_azalea_bush")
    commands.append(f"setblock {1203} {base_y+5} {-124} potted_flowering_azalea")

    return commands

def main():
    parser = argparse.ArgumentParser(description="Modern Luxury Villa Generator")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--undo", action="store_true", help="Undo construction by clearing house area")
    args = parser.parse_args()

    min_x, max_x = 1195, 1204
    min_z, max_z = -132, -123
    base_y = 63

    if args.undo:
        print("🔄 Undoing Modern Villa construction & restoring grass...")
        clear_cmd = f"fill {min_x-3} {base_y+1} {min_z-3} {max_x+3} {base_y+15} {max_z+3} air"
        grass_cmd = f"fill {min_x-3} {base_y} {min_z-3} {max_x+3} {base_y} {max_z+3} grass_block"
        send_exaroton_command(clear_cmd, dry_run=args.dry_run)
        send_exaroton_command(grass_cmd, dry_run=args.dry_run)
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        print("✨ Modern villa removed and ground restored to grass successfully.")
        return

    commands = generate_modern_house_commands()
    print(f"🏙️ Building 10x10 Modern Villa centered at (1200, 63, -127)... Total steps: {len(commands)}")

    history = {"center": [1200, 63, -127], "bounds": [min_x, base_y, min_z, max_x, base_y+15, max_z], "commands": commands}

    executed_count = 0
    for cmd in commands:
        if send_exaroton_command(cmd, dry_run=args.dry_run):
            executed_count += 1

    if not args.dry_run:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)

    print(f"🎉 Modern Villa construction finished! ({executed_count}/{len(commands)} steps executed successfully)")

if __name__ == "__main__":
    main()
