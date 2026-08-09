#!/usr/bin/env python3
"""
Automated Minecraft Standard High-Yield Mob XP Farm Generator (Lightproof Shaft Fix)
--------------------------------------------------------------------------------------
Builds a classic 20x20 spawning chamber Mob XP Tower Farm centered above (1197, 63, -127).

Lightproof Fixes:
- The drop shaft walls extend fully around the 2x2 chute from Y=65 up to Y=86.
- The front killing opening at Y=65 is fitted with Oak Trapdoors / Slabs / Darkened Glass
  so player can strike mob feet without sunlight/sky light leaking upward into the top chamber!
- Light levels inside the upper spawning chamber remain strictly at 0 even during bright daylight.

Note: Prepared script only. Do NOT run build command until requested by user.

Usage:
  python3 build_xp_farm.py [--dry-run]
  python3 build_xp_farm.py --undo [--dry-run]
"""

import os
import sys
import json
import subprocess
import argparse

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                CONFIG[k.strip()] = v.strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID")
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "xp_farm_history.json")

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

def build_xp_farm(dry_run=False):
    commands = []
    
    # 1. Clear region above Y=63 floor for large farm (20x20: X 1187..1208, Z -138..-115)
    commands.append("execute in minecraft:overworld run fill 1187 64 -138 1208 92 -115 minecraft:air")

    # 2. Collection & AFK Spot at Y=64
    commands.append("execute in minecraft:overworld run setblock 1196 64 -127 minecraft:chest[facing=east]")
    commands.append("execute in minecraft:overworld run setblock 1196 64 -126 minecraft:chest[facing=east]")
    
    # 4 Hoppers feeding chest
    commands.append("execute in minecraft:overworld run setblock 1197 64 -127 minecraft:hopper[facing=west]")
    commands.append("execute in minecraft:overworld run setblock 1197 64 -126 minecraft:hopper[facing=west]")
    commands.append("execute in minecraft:overworld run setblock 1198 64 -127 minecraft:hopper[facing=west]")
    commands.append("execute in minecraft:overworld run setblock 1198 64 -126 minecraft:hopper[facing=west]")
    
    # Slabs on hoppers at Y=65
    commands.append("execute in minecraft:overworld run fill 1197 65 -127 1198 65 -126 minecraft:smooth_stone_slab[type=bottom]")

    # 3. Lightproof Fall Shaft (Y=65 to Y=86)
    commands.append("execute in minecraft:overworld run fill 1196 65 -128 1199 86 -128 minecraft:cobblestone") # North wall
    commands.append("execute in minecraft:overworld run fill 1196 65 -125 1199 86 -125 minecraft:cobblestone") # South wall
    commands.append("execute in minecraft:overworld run fill 1196 65 -127 1196 86 -126 minecraft:cobblestone") # West wall
    commands.append("execute in minecraft:overworld run fill 1199 65 -127 1199 86 -126 minecraft:cobblestone") # East wall

    # Light-blocking Trapdoors at hit opening Y=65 (allows attacking feet while blocking light going up shaft)
    commands.append("execute in minecraft:overworld run setblock 1196 65 -127 minecraft:oak_trapdoor[open=false,half=top,facing=west]")
    commands.append("execute in minecraft:overworld run setblock 1196 65 -126 minecraft:oak_trapdoor[open=false,half=top,facing=west]")

    # Water stopper signs at Y=86 inside shaft
    commands.append("execute in minecraft:overworld run setblock 1197 86 -127 minecraft:oak_sign[rotation=0]")
    commands.append("execute in minecraft:overworld run setblock 1197 86 -126 minecraft:oak_sign[rotation=0]")
    commands.append("execute in minecraft:overworld run setblock 1198 86 -127 minecraft:oak_sign[rotation=0]")
    commands.append("execute in minecraft:overworld run setblock 1198 86 -126 minecraft:oak_sign[rotation=0]")

    # 4. Spawning Platforms (4 corner platforms, 8x8 each, at Y=87)
    # NW: 1189..1196, -136..-129
    commands.append("execute in minecraft:overworld run fill 1189 87 -136 1196 87 -129 minecraft:cobblestone")
    # NE: 1199..1206, -136..-129
    commands.append("execute in minecraft:overworld run fill 1199 87 -136 1206 87 -129 minecraft:cobblestone")
    # SW: 1189..1196, -124..-117
    commands.append("execute in minecraft:overworld run fill 1189 87 -124 1196 87 -117 minecraft:cobblestone")
    # SE: 1199..1206, -124..-117
    commands.append("execute in minecraft:overworld run fill 1199 87 -124 1206 87 -117 minecraft:cobblestone")

    # 5. Sunken Water Canals (Y=86 floors)
    commands.append("execute in minecraft:overworld run fill 1197 86 -136 1198 86 -129 minecraft:cobblestone") # North
    commands.append("execute in minecraft:overworld run fill 1197 86 -124 1198 86 -117 minecraft:cobblestone") # South
    commands.append("execute in minecraft:overworld run fill 1189 86 -127 1196 86 -126 minecraft:cobblestone") # West
    commands.append("execute in minecraft:overworld run fill 1199 86 -127 1206 86 -126 minecraft:cobblestone") # East

    # Open Trapdoors along platform edges at Y=87
    commands.append("execute in minecraft:overworld run fill 1196 87 -136 1196 87 -129 minecraft:oak_trapdoor[open=true,facing=east]")
    commands.append("execute in minecraft:overworld run fill 1199 87 -136 1199 87 -129 minecraft:oak_trapdoor[open=true,facing=west]")
    commands.append("execute in minecraft:overworld run fill 1196 87 -124 1196 87 -117 minecraft:oak_trapdoor[open=true,facing=east]")
    commands.append("execute in minecraft:overworld run fill 1199 87 -124 1199 87 -117 minecraft:oak_trapdoor[open=true,facing=west]")
    commands.append("execute in minecraft:overworld run fill 1189 87 -128 1196 87 -128 minecraft:oak_trapdoor[open=true,facing=south]")
    commands.append("execute in minecraft:overworld run fill 1189 87 -125 1196 87 -125 minecraft:oak_trapdoor[open=true,facing=north]")
    commands.append("execute in minecraft:overworld run fill 1199 87 -128 1206 87 -128 minecraft:oak_trapdoor[open=true,facing=south]")
    commands.append("execute in minecraft:overworld run fill 1199 87 -125 1206 87 -125 minecraft:oak_trapdoor[open=true,facing=north]")

    # 6. Outer Chamber Walls (Y=87 to Y=89)
    commands.append("execute in minecraft:overworld run fill 1188 87 -137 1207 89 -137 minecraft:cobblestone") # North
    commands.append("execute in minecraft:overworld run fill 1188 87 -116 1207 89 -116 minecraft:cobblestone") # South
    commands.append("execute in minecraft:overworld run fill 1188 87 -137 1188 89 -116 minecraft:cobblestone") # West
    commands.append("execute in minecraft:overworld run fill 1207 87 -137 1207 89 -116 minecraft:cobblestone") # East

    # Water Sources at canal ends (Y=87)
    commands.append("execute in minecraft:overworld run setblock 1197 87 -136 minecraft:water")
    commands.append("execute in minecraft:overworld run setblock 1198 87 -136 minecraft:water")
    commands.append("execute in minecraft:overworld run setblock 1197 87 -117 minecraft:water")
    commands.append("execute in minecraft:overworld run setblock 1198 87 -117 minecraft:water")
    commands.append("execute in minecraft:overworld run setblock 1189 87 -127 minecraft:water")
    commands.append("execute in minecraft:overworld run setblock 1189 87 -126 minecraft:water")
    commands.append("execute in minecraft:overworld run setblock 1206 87 -127 minecraft:water")
    commands.append("execute in minecraft:overworld run setblock 1206 87 -126 minecraft:water")

    # 7. Roof at Y=90 & Lighting at Y=91
    commands.append("execute in minecraft:overworld run fill 1187 90 -138 1208 90 -115 minecraft:cobblestone")
    commands.append("execute in minecraft:overworld run fill 1188 91 -137 1207 91 -116 minecraft:torch replace minecraft:air")

    # Save history
    history = {"commands": commands, "base": {"x": 1197, "y": 63, "z": -127}, "bounds": "lightproof_20x20"}
    if not dry_run:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)

    print(f"🔨 Executing {len(commands)} commands to build Lightproof Mob XP Farm...")
    for cmd in commands:
        send_exaroton_command(cmd, dry_run=dry_run)

def undo_xp_farm(dry_run=False):
    print("🔄 Undoing Mob XP Farm construction...")
    clear_cmd = "execute in minecraft:overworld run fill 1187 64 -138 1208 92 -115 minecraft:air"
    send_exaroton_command(clear_cmd, dry_run=dry_run)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Lightproof Mob XP Farm")
    parser.add_argument("--dry-run", action="store_true", help="Preview commands")
    parser.add_argument("--undo", action="store_true", help="Undo construction")
    args = parser.parse_args()

    if args.undo:
        undo_xp_farm(dry_run=args.dry_run)
    else:
        build_xp_farm(dry_run=args.dry_run)
