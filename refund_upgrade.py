#!/usr/bin/env python3
"""
Advanced Minecraft Server Refund & Rollback Script
--------------------------------------------------
Automates the process of removing region protections (WorldGuard flags),
downsizing plots, removing trade records from Shopkeepers processed trades,
and issuing full or partial emerald refunds to players.

Usage:
  python3 refund_upgrade.py <player_name> <upgrade_type> [options]

Examples:
  # Full refund for hanansaleh's PvP protection:
  python3 refund_upgrade.py hanansaleh pvp

  # 50% partial refund for mustafahacker67's Creeper protection:
  python3 refund_upgrade.py mustafahacker67 creeper --percent 50

  # Refund all protections and downsize plot to small:
  python3 refund_upgrade.py hanansaleh all --downsize small
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

PROCESSED_FILE = "Shopkeepers/processed_trades.json"
REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"

# Player Username to WorldGuard Region Mapping
PLAYER_REGION_MAP = {
    "hanansaleh": "hanansaleh",
    ".mustafahacker67": "mustafahacker67",
    "mustafahacker67": "mustafahacker67",
    ".HastyBag7675": "hastybag7675_manansaleh2007",
    "HastyBag7675": "hastybag7675_manansaleh2007",
    ".WiryCircle3938": "wirycircle3938",
    "WiryCircle3938": "wirycircle3938",
    "manansaleh2007": "hastybag7675_manansaleh2007",
    "NightmareDady": "nightmaredady",
    "nightmaredady": "nightmaredady",
    ".AzanSaleh": "azansalehhh",
    "AzanSaleh": "azansalehhh",
    "azansalehhh": "azansalehhh"
}

# Upgrades Configuration (Name, WorldGuard flag, Emerald Cost)
UPGRADES = {
    "tnt": {
        "name": "TNT Protection",
        "flag": "tnt",
        "cost": 32
    },
    "creeper": {
        "name": "Creeper & Explosion Protection",
        "flag": "other-explosion",
        "cost": 32
    },
    "pvp": {
        "name": "PvP Protection",
        "flag": "pvp",
        "extra_flags": ["pvp-group"],
        "cost": 48
    },
    "mob": {
        "name": "Mob Spawn Protection",
        "flag": "mob-spawning",
        "cost": 64
    },
    "fire": {
        "name": "Fire Spread Protection",
        "flag": "fire-spread",
        "cost": 24
    },
    "small_plot": {
        "name": "Small Plot Expansion (12x12)",
        "flag": None,
        "cost": 32
    }
}

def get_region_for_player(player_name):
    if player_name in PLAYER_REGION_MAP:
        return PLAYER_REGION_MAP[player_name]
    clean = player_name.lower().replace(".", "")
    if clean in PLAYER_REGION_MAP:
        return PLAYER_REGION_MAP[clean]
    return clean

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
    pull_cmd = [sys.executable, "sync.py", "pull", REGIONS_FILE]
    subprocess.run(pull_cmd, capture_output=True)

def push_processed_trades():
    push_cmd = [sys.executable, "sync.py", "push", PROCESSED_FILE]
    subprocess.run(push_cmd, capture_output=True)

def get_region_flags(region_name):
    pull_region_file()
    if not os.path.exists(REGIONS_FILE):
        return {}

    flags = {}
    current_region = None
    flags_lines = []
    in_flags = False

    with open(REGIONS_FILE, "r") as f:
        for line in f:
            region_match = re.match(r"^ {4}([a-zA-Z0-9_\-]+):", line)
            if region_match:
                if current_region == region_name and flags_lines:
                    break
                current_region = region_match.group(1)
                flags_lines = []
                in_flags = False
                continue

            if current_region == region_name:
                if "flags:" in line:
                    in_flags = True
                    content = line.split("flags:", 1)[1].strip()
                    flags_lines.append(content)
                    if content.endswith("}"):
                        in_flags = False
                    continue
                
                if in_flags:
                    content = line.strip()
                    flags_lines.append(content)
                    if content.endswith("}"):
                        in_flags = False
                    continue

    if flags_lines:
        full_content = " ".join(flags_lines).strip()
        if full_content.startswith("{") and full_content.endswith("}"):
            inner = full_content[1:-1].strip()
            if inner:
                pairs = inner.split(",")
                for pair in pairs:
                    if ":" in pair:
                        k, v = pair.split(":", 1)
                        flags[k.strip()] = v.strip()
    return flags

def refund_upgrade(player, upgrade_type, percent=100, downsize_category=None, dry_run=False):
    region_name = get_region_for_player(player)
    print(f"🔄 Starting refund process for {player} (Region: {region_name})...")
    
    # 1. Gather active flags
    active_flags = get_region_flags(region_name)
    
    # Determine upgrades to process
    targets = []
    if upgrade_type == "all":
        targets = list(UPGRADES.keys())
    elif upgrade_type in UPGRADES:
        targets = [upgrade_type]
    else:
        print(f"❌ Unknown upgrade type: {upgrade_type}. Choices: {list(UPGRADES.keys())} or 'all'")
        sys.exit(1)

    total_refund = 0
    flags_to_remove = []
    
    for t in targets:
        cfg = UPGRADES[t]
        flag = cfg["flag"]
        
        # Check if it has a flag and if it is active
        is_active = False
        if flag:
            if flag in active_flags:
                is_active = True
                flags_to_remove.append(flag)
                if "extra_flags" in cfg:
                    flags_to_remove.extend(cfg["extra_flags"])
        else:
            # For non-flag upgrades like plot expansions, we check if they want to downsize or refund it anyway
            is_active = True
            
        if is_active:
            cost = cfg["cost"]
            refund_val = int(cost * (percent / 100.0))
            total_refund += refund_val
            print(f"💎 Detected: {cfg['name']} (Cost: {cost} Emeralds, Refund: {refund_val} Emeralds)")
        else:
            print(f"ℹ️ {cfg['name']} is not currently active on region '{region_name}'.")

    if total_refund == 0 and not downsize_category:
        print("⚠️ No active upgrades found to refund for this region.")
        return

    # 2. Perform WorldGuard flag removals
    if flags_to_remove:
        print(f"🛡️ Removing flags: {flags_to_remove}")
        for flag in flags_to_remove:
            send_exaroton_command(f"rg flag -w \"world\" {region_name} {flag} none", dry_run)
        send_exaroton_command("wg save", dry_run)

    # 3. Downsize plot if requested
    if downsize_category:
        print(f"📐 Downsizing plot '{region_name}' to '{downsize_category}' category...")
        if dry_run:
            print(f"[DRY-RUN] Would run: python3 resize_plot.py {region_name} {downsize_category}")
        else:
            resize_cmd = [sys.executable, "resize_plot.py", region_name, downsize_category]
            res = subprocess.run(resize_cmd, capture_output=True, text=True)
            print(res.stdout)

    # 4. Issue the Emerald refund
    if total_refund > 0:
        print(f"💰 Refunding {total_refund} Emeralds to player '{player}'...")
        send_exaroton_command(f"give {player} minecraft:emerald {total_refund}", dry_run)

    # 5. Clean up processed trades file
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, "r") as f:
                processed = json.load(f)
        except Exception:
            processed = []

        initial_len = len(processed)
        new_processed = []
        for key in processed:
            # Key format: timestamp_player_result_type
            match_player = f"_{player}_" in key or key.endswith(f"_{player}")
            
            # Match upgrade type keywords in the trade key or results
            match_upgrade = False
            if upgrade_type == "all":
                match_upgrade = True
            else:
                # We check if this key corresponds to the target upgrades
                # Since the original trade was a WRITTEN_BOOK, player matches are usually sufficient to clear their upgrades
                match_upgrade = True 
            
            if match_player and match_upgrade:
                print(f"🗑️ Removing trade record from history: {key}")
                continue
            new_processed.append(key)

        if len(new_processed) < initial_len:
            if not dry_run:
                with open(PROCESSED_FILE, "w") as f:
                    json.dump(new_processed, f)
                push_processed_trades()
                print("📝 Processed trades list updated and pushed to server.")
            else:
                print(f"[DRY-RUN] Would remove {initial_len - len(new_processed)} trade record(s) from processed_trades.json")

    print("🎉 Refund and rollback process completed!")

def main():
    parser = argparse.ArgumentParser(description="Advanced Upgrade Refund & Rollback Tool")
    parser.add_argument("player", help="Minecraft Bedrock/Java username of the player")
    parser.add_argument("type", choices=list(UPGRADES.keys()) + ["all"], help="Type of upgrade to refund")
    parser.add_argument("--percent", type=int, default=100, help="Percentage of cost to refund (default: 100)")
    parser.add_argument("--downsize", choices=["small", "normal", "big", "large"], help="Optional category to downsize the region bounds to")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be executed without running server commands or saving changes")

    args = parser.parse_args()
    refund_upgrade(
        player=args.player,
        upgrade_type=args.type,
        percent=args.percent,
        downsize_category=args.downsize,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()
