#!/usr/bin/env python3
"""
Plot Sizer & Cutter Script for WorldGuard Regions (with Undo Support)
----------------------------------------------------------------------
Resizes or cuts WorldGuard region bounds based on target plot size categories:
  - small  : 8x8 blocks
  - normal : 15x15 blocks
  - big    : 30x30 blocks

Maintains a local backup of the previous bounds in
`WorldGuard/backups/<region>_bounds.json` to support a strict `--undo` operation.

Usage:
  python3 resize_plot.py <region_name> <small|normal|big> [--height H] [--world WORLD]
  python3 resize_plot.py <region_name> --undo [--world WORLD]

Example:
  # Resize to normal:
  python3 resize_plot.py manansaleh2007_farm normal --height 15

  # Undo the resize:
  python3 resize_plot.py manansaleh2007_farm --undo
"""

import os
import sys
import json
import re
import subprocess
import argparse

# Load Environment Configuration (.env)
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

PLOT_SIZES = {
    "small": 8,
    "normal": 15,
    "big": 30,
    "large": 30
}

BACKUP_DIR = "WorldGuard/backups"

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
            print(f"✅ Executed console command: {cmd}")
            return True
        else:
            print(f"❌ Exaroton Command Error: {data.get('error')} | Output: {res.stdout}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def pull_region_file():
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-H", f"Authorization: Bearer {TOKEN}",
        f"https://api.exaroton.com/v1/servers/{SERVER_ID}/files/data/plugins/WorldGuard/worlds/world/regions.yml"
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    if res.stdout and "regions:" in res.stdout:
        os.makedirs("WorldGuard/worlds/world", exist_ok=True)
        with open("WorldGuard/worlds/world/regions.yml", "w") as f:
            f.write(res.stdout)
        return True
    return False

def parse_region_bounds(region_name):
    filepath = "WorldGuard/worlds/world/regions.yml"
    if not os.path.exists(filepath):
        pull_region_file()

    if not os.path.exists(filepath):
        print("❌ Could not pull regions file from Exaroton server.")
        sys.exit(1)

    current_region = None
    min_coords = None
    max_coords = None

    with open(filepath, "r") as f:
        for line in f:
            reg_match = re.match(r"^ {4}([a-zA-Z0-9_\-]+):", line)
            if reg_match:
                current_region = reg_match.group(1)
                continue

            if current_region == region_name:
                if "min:" in line:
                    m = re.search(r"x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)", line)
                    if m:
                        min_coords = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
                elif "max:" in line:
                    m = re.search(r"x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)", line)
                    if m:
                        max_coords = (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    return min_coords, max_coords

def save_bounds_backup(region_name, min_coords, max_coords):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_file = os.path.join(BACKUP_DIR, f"{region_name}_bounds.json")
    with open(backup_file, "w") as f:
        json.dump({
            "min": min_coords,
            "max": max_coords
        }, f, indent=4)
    print(f"📝 Bounds backup saved to '{backup_file}'.")

def load_bounds_backup(region_name):
    backup_file = os.path.join(BACKUP_DIR, f"{region_name}_bounds.json")
    if not os.path.exists(backup_file):
        return None
    try:
        with open(backup_file, "r") as f:
            return json.load(f)
    except Exception:
        return None

def resize_plot(region_name, category, custom_height=None, world="world", dry_run=False):
    target_dim = PLOT_SIZES.get(category.lower())
    if not target_dim:
        print(f"❌ Unknown size category: {category}. Choose from: small (8x8), normal (15x15), big/large (30x30)")
        sys.exit(1)

    print(f"🔍 Pulling current region data for '{region_name}'...")
    pull_region_file()
    min_c, max_c = parse_region_bounds(region_name)

    if not min_c or not max_c:
        print(f"❌ Region '{region_name}' not found in WorldGuard regions.yml.")
        sys.exit(1)

    # 1. Back up current bounds before resizing
    save_bounds_backup(region_name, min_c, max_c)

    cur_min_x, cur_min_y, cur_min_z = min_c
    cur_max_x, cur_max_y, cur_max_z = max_c

    # Center point of existing plot
    center_x = (cur_min_x + cur_max_x) // 2
    center_z = (cur_min_z + cur_max_z) // 2

    # Calculate centered new X and Z bounds
    half_size = target_dim // 2
    new_min_x = center_x - half_size
    new_max_x = new_min_x + target_dim - 1

    new_min_z = center_z - half_size
    new_max_z = new_min_z + target_dim - 1

    # Y bounds (Height)
    if custom_height:
        new_min_y = cur_min_y
        new_max_y = cur_min_y + custom_height - 1
    else:
        new_min_y = cur_min_y
        new_max_y = cur_max_y

    width = (new_max_x - new_min_x) + 1
    length = (new_max_z - new_min_z) + 1
    height = (new_max_y - new_min_y) + 1

    print(f"📐 Resizing Region '{region_name}' to category '{category.upper()}' ({target_dim}x{target_dim}):")
    print(f"   X: {new_min_x} to {new_max_x} (Width: {width})")
    print(f"   Y: {new_min_y} to {new_max_y} (Height: {height})")
    print(f"   Z: {new_min_z} to {new_max_z} (Length: {length})")

    # Command to redefine region in WorldGuard console
    cmd = f"rg redefine -w {world} {region_name} {new_min_x} {new_min_y} {new_min_z} {new_max_x} {new_max_y} {new_max_z}"
    
    if send_exaroton_command(cmd, dry_run):
        send_exaroton_command(f"rg save -w {world}", dry_run)
        send_exaroton_command("wg save", dry_run)
        send_exaroton_command("rg reload", dry_run)
        print(f"🎉 Successfully updated region '{region_name}' on the server!")

def main():
    parser = argparse.ArgumentParser(description="WorldGuard Region Plot Sizer & Cutter with Rollback")
    parser.add_argument("region", help="WorldGuard region ID (e.g. manansaleh2007_farm)")
    parser.add_argument("category", nargs="?", choices=["small", "normal", "big", "large"], help="Target size category. Optional if running --undo")
    parser.add_argument("--height", type=int, help="Optional custom height in blocks")
    parser.add_argument("--world", default="world", help="World name (default: world)")
    parser.add_argument("--undo", action="store_true", help="Undo the last resize operation for this region")
    parser.add_argument("--dry-run", action="store_true", help="Preview command without executing on the server")

    args = parser.parse_args()

    if args.undo:
        backup = load_bounds_backup(args.region)
        if not backup:
            print(f"❌ No bounds backup found for region '{args.region}'. Cannot undo.")
            sys.exit(1)
            
        min_x, min_y, min_z = backup["min"]
        max_x, max_y, max_z = backup["max"]
        
        print(f"🔄 Reverting region '{args.region}' bounds to backup state:")
        print(f"   Min: X={min_x}, Y={min_y}, Z={min_z}")
        print(f"   Max: X={max_x}, Y={max_y}, Z={max_z}")
        
        cmd = f"rg redefine -w {args.world} {args.region} {min_x} {min_y} {min_z} {max_x} {max_y} {max_z}"
        if send_exaroton_command(cmd, args.dry_run):
            send_exaroton_command(f"rg save -w {args.world}", args.dry_run)
            send_exaroton_command("wg save", args.dry_run)
            send_exaroton_command("rg reload", args.dry_run)
            print(f"🎉 Bounds for region '{args.region}' successfully restored!")
        return

    if not args.category:
        print("❌ Error: category argument is required unless running with --undo")
        sys.exit(1)

    resize_plot(args.region, args.category, custom_height=args.height, world=args.world, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
