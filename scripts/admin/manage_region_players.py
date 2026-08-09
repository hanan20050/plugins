#!/usr/bin/env python3
"""
WorldGuard Region Access & Membership Manager (with Undo Support)
-----------------------------------------------------------------
Manages region owners and members via Exaroton console commands. Automatically
resolves real player names to Bedrock/Geyser usernames, executes commands, and
synchronizes local configuration. Maintains a player backup database in
`WorldGuard/backups/<region>_players.json` to support strict `--undo` operations.

Usage:
  python3 manage_region_players.py <region_name> <addowner|removeowner|addmember|removemember> <player_name> [--dry-run]
  python3 manage_region_players.py <region_name> --undo [--dry-run]

Examples:
  # Add NightmareDady (rayan saleh) as owner of manan_farm:
  python3 manage_region_players.py manan_farm addowner rayan

  # Undo the last player membership modification:
  python3 manage_region_players.py manan_farm --undo
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
REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"
BACKUP_DIR = "WorldGuard/backups"

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

def parse_current_players(region_name):
    pull_region_file()
    if not os.path.exists(REGIONS_FILE):
        return {"owners": [], "members": []}

    owners = []
    members = []
    current_region = None
    in_owners = False
    in_members = False

    with open(REGIONS_FILE, "r") as f:
        for line in f:
            reg_match = re.match(r"^ {4}([a-zA-Z0-9_\-]+):", line)
            if reg_match:
                current_region = reg_match.group(1)
                in_owners = False
                in_members = False
                continue

            if current_region == region_name:
                if "owners:" in line:
                    in_owners = True
                    in_members = False
                    continue
                if "members:" in line:
                    in_members = True
                    in_owners = False
                    continue
                
                # Check for list items or brackets under owners/members
                if in_owners:
                    # check for unique-ids or players lists
                    m = re.search(r"(unique-ids|players):\s*\[(.*?)\]", line)
                    if m:
                        items = [x.strip() for x in m.group(2).split(",") if x.strip()]
                        owners.extend(items)
                    # YAML list item format
                    m_list = re.search(r"-\s+([a-zA-Z0-9_\-\.]+)", line)
                    if m_list and not "unique-ids" in line and not "players" in line:
                        owners.append(m_list.group(1).strip())
                elif in_members:
                    m = re.search(r"(unique-ids|players):\s*\[(.*?)\]", line)
                    if m:
                        items = [x.strip() for x in m.group(2).split(",") if x.strip()]
                        members.extend(items)
                    m_list = re.search(r"-\s+([a-zA-Z0-9_\-\.]+)", line)
                    if m_list and not "unique-ids" in line and not "players" in line:
                        members.append(m_list.group(1).strip())
                        
            # If we match another region indent, we are done
            if current_region and line.startswith("    ") and not line.startswith("        ") and current_region != region_name:
                if len(owners) > 0 or len(members) > 0:
                    break

    return {"owners": list(set(owners)), "members": list(set(members))}

def save_player_backup(region_name, players_dict):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_file = os.path.join(BACKUP_DIR, f"{region_name}_players.json")
    with open(backup_file, "w") as f:
        json.dump(players_dict, f, indent=4)
    print(f"📝 Region player backup saved to '{backup_file}'.")

def load_player_backup(region_name):
    backup_file = os.path.join(BACKUP_DIR, f"{region_name}_players.json")
    if not os.path.exists(backup_file):
        return None
    try:
        with open(backup_file, "r") as f:
            return json.load(f)
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser(description="Manage WorldGuard Region Access & Membership with Rollback")
    parser.add_argument("region", help="Name of the WorldGuard region")
    parser.add_argument("action", nargs="?", choices=["addowner", "removeowner", "addmember", "removemember"], help="Access modification action")
    parser.add_argument("player", nargs="?", help="Real name or username of the player")
    parser.add_argument("--undo", action="store_true", help="Undo the last access changes and restore previous members/owners")
    parser.add_argument("--dry-run", action="store_true", help="Preview commands without executing on the server")

    args = parser.parse_args()

    if args.undo:
        # Load player backup
        backup = load_player_backup(args.region)
        if not backup:
            print(f"❌ No player membership backup found for region '{args.region}'. Cannot undo.")
            sys.exit(1)
            
        print(f"🔄 Reverting region '{args.region}' memberships to backup state:")
        print(f"   Owners: {backup['owners']}")
        print(f"   Members: {backup['members']}")
        
        # 1. Clear all owners and members on the server
        send_exaroton_command(f"rg removeowner -w \"world\" {args.region} -a", args.dry_run)
        send_exaroton_command(f"rg removemember -w \"world\" {args.region} -a", args.dry_run)
        
        # 2. Add back owners and members
        for owner in backup["owners"]:
            send_exaroton_command(f"rg addowner -w \"world\" {args.region} {owner}", args.dry_run)
        for member in backup["members"]:
            send_exaroton_command(f"rg addmember -w \"world\" {args.region} {member}", args.dry_run)
            
        send_exaroton_command("wg save", args.dry_run)
        
        if not args.dry_run:
            print("🔄 Pulling updated regions config to local workspace...")
            pull_region_file()
            
        print("🎉 Region memberships restored successfully!")
        return

    # Check required arguments for standard mode
    if not args.action or not args.player:
        print("❌ Error: action and player arguments are required unless running with --undo")
        sys.exit(1)

    # 1. Back up current players before changes
    current_players = parse_current_players(args.region)
    save_player_backup(args.region, current_players)

    # 2. Resolve player username and run command
    resolved_player = resolve_player_username(args.player)
    print(f"👤 Resolved player name '{args.player}' to username '{resolved_player}'")
    
    wg_cmd = f"rg {args.action} -w \"world\" {args.region} {resolved_player}"
    
    if send_exaroton_command(wg_cmd, args.dry_run):
        send_exaroton_command("wg save", args.dry_run)
        
        if not args.dry_run:
            print("🔄 Pulling updated regions config to local workspace...")
            pull_region_file()
            
        print(f"🎉 Successfully completed player region management command!")

if __name__ == "__main__":
    main()
