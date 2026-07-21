#!/usr/bin/env python3
"""
WorldGuard Region Access & Membership Manager
---------------------------------------------
Manages region owners and members via Exaroton console commands. Automatically
resolves real player names to Bedrock/Geyser usernames, executes commands, and
synchronizes local configuration.

Usage:
  python3 manage_region_players.py <region_name> <addowner|removeowner|addmember|removemember> <player_name> [--dry-run]

Examples:
  # Add NightmareDady (rayan saleh) as owner of manan_farm:
  python3 manage_region_players.py manan_farm addowner rayan

  # Remove mustafa from a region:
  python3 manage_region_players.py some_plot removemember mustafa
"""

import os
import sys
import json
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
REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"

# Player Real Name to Minecraft Username Mapping
PLAYER_IDENTITY_MAP = {
    "mustafa": ".mustafahacker67",
    "mustafahacker67": ".mustafahacker67",
    "muhammad saleh": ".HastyBag7675",
    "muhammad": ".HastyBag7675",
    "hastybag": ".HastyBag7675",
    "omer saleh": ".WiryCircle3938",
    "omer": ".WiryCircle3938",
    "wirycircle": ".WiryCircle3938",
    "hanan saleh": "hanansaleh",
    "hanan": "hanansaleh",
    "manan saleh": "manansaleh2007",
    "manan": "manansaleh2007",
    "rayan saleh": "NightmareDady",
    "rayan": "NightmareDady",
    "nightmaredady": "NightmareDady",
    "azan saleh": ".AzanSaleh",
    "azan": ".AzanSaleh",
    "azansalehhh": "azansalehhh"
}

def resolve_player_username(name):
    clean_name = name.strip().lower()
    if clean_name in PLAYER_IDENTITY_MAP:
        return PLAYER_IDENTITY_MAP[clean_name]
    # Default back to whatever is passed if not matched
    return name

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
            print(f"❌ Exaroton Command Error: {data.get('error')}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def pull_region_file():
    pull_cmd = [sys.executable, "sync.py", "pull", REGIONS_FILE]
    subprocess.run(pull_cmd, capture_output=True)

def main():
    parser = argparse.ArgumentParser(description="Manage WorldGuard Region Access & Membership")
    parser.add_argument("region", help="Name of the WorldGuard region")
    parser.add_argument("action", choices=["addowner", "removeowner", "addmember", "removemember"], help="Access modification action")
    parser.add_argument("player", help="Real name or username of the player")
    parser.add_argument("--dry-run", action="store_true", help="Preview command without executing on the server")

    args = parser.parse_args()
    
    resolved_player = resolve_player_username(args.player)
    print(f"👤 Resolved player name '{args.player}' to username '{resolved_player}'")
    
    # Construct WorldGuard command
    # Syntax: rg <action> -w "world" <region> <player>
    wg_cmd = f"rg {args.action} -w \"world\" {args.region} {resolved_player}"
    
    # Run the change command
    if send_exaroton_command(wg_cmd, args.dry_run):
        # Save WorldGuard changes to database/disk
        send_exaroton_command("wg save", args.dry_run)
        
        # Pull final config files back local to keep git sync
        if not args.dry_run:
            print("🔄 Pulling updated regions config to local workspace...")
            pull_region_file()
            
        print(f"🎉 Successfully completed player region management command!")

if __name__ == "__main__":
    main()
