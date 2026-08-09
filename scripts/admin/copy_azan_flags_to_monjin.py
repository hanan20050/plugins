#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import re

# Load environment variables
ENV_FILE = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if not os.path.exists(ENV_FILE):
    ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")

CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    CONFIG[parts[0].strip()] = parts[1].strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or "cEuS61sZvNEFS3aB"

BACKUP_FILE = os.path.join(os.path.dirname(__file__), "WorldGuard", "backups", "mon_jin_flags_backup.json")
if not os.path.isabs(BACKUP_FILE):
    BACKUP_FILE = "/Users/hanansaleh/Downloads/plugins/WorldGuard/backups/mon_jin_flags_backup.json"

def send_exaroton_command(cmd):
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
            print(f"✅ Console command executed: {cmd}")
            return True
        else:
            print(f"❌ Error executing command '{cmd}': {data.get('error')}")
            return False
    except Exception as e:
        print(f"Response Error: {res.stdout}")
        return False

def sync_pull_regions():
    print("Pulling updated regions.yml from server...")
    res = subprocess.run([sys.executable, "sync.py", "pull", "WorldGuard/worlds/world/regions.yml", "--force"], capture_output=True, text=True)
    print(res.stdout)

def parse_flags_from_yaml(regions_file, region_id):
    if not os.path.exists(regions_file):
        return {}
    
    with open(regions_file, "r") as f:
        content = f.read()

    # Find the region entry block
    pattern = rf"^\s+{region_id}:\s*\n(.*?)(?=^\s+\w+:|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        return {}
    
    block = match.group(1)
    # Find the flags line within this block. It can be single-line or multi-line
    # e.g., flags: {other-explosion: deny, creeper-explosion: deny, tnt: deny, pvp: deny,
    #             pvp-group: NON_OWNERS}
    flags_match = re.search(r"flags:\s*\{(.*?)\}", block, re.DOTALL)
    if not flags_match:
        return {}
    
    flags_str = flags_match.group(1).replace("\n", "").replace("\r", "")
    # Parse individual key-value pairs
    flags = {}
    # split by comma, but be careful with formatting
    parts = flags_str.split(",")
    for part in parts:
        part = part.strip()
        if ":" in part:
            k, v = part.split(":", 1)
            flags[k.strip()] = v.strip()
    return flags

def main():
    # 1. Pull latest regions
    sync_pull_regions()

    regions_file = "/Users/hanansaleh/Downloads/plugins/WorldGuard/worlds/world/regions.yml"
    
    # Get original flags
    original_flags = parse_flags_from_yaml(regions_file, "mon_jin_deku")
    print(f"Current mon_jin_deku flags: {original_flags}")

    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    
    if "--undo" in sys.argv:
        if not os.path.exists(BACKUP_FILE):
            print("❌ Backup file not found for undo.")
            sys.exit(1)
        with open(BACKUP_FILE, "r") as f:
            backup_data = json.load(f)
        
        saved_flags = backup_data.get("original_flags", {})
        print(f"🔄 Rolling back flags for mon_jin_deku to: {saved_flags}")
        
        # Clear existing flags first
        for flag in ["other-explosion", "creeper-explosion", "tnt", "pvp"]:
            send_exaroton_command(f'rg flag -w "world" mon_jin_deku {flag}')
        
        # Apply saved flags
        for flag, value in saved_flags.items():
            if flag == "pvp-group":
                base_pvp = saved_flags.get("pvp", "allow")
                send_exaroton_command(f'rg flag -w "world" mon_jin_deku -g {value} pvp {base_pvp}')
            elif flag == "pvp":
                if "pvp-group" not in saved_flags:
                    send_exaroton_command(f'rg flag -w "world" mon_jin_deku pvp {value}')
            else:
                send_exaroton_command(f'rg flag -w "world" mon_jin_deku {flag} {value}')
                
        send_exaroton_command("wg save")
        send_exaroton_command("rg reload")
        sync_pull_regions()
        print("✅ Undo completed successfully!")
        return

    # Normal execution: copy flags
    backup_payload = {
        "original_flags": original_flags,
        "timestamp": subprocess.getoutput("date -u +'%Y-%m-%dT%H:%M:%SZ'")
    }
    with open(BACKUP_FILE, "w") as f:
        json.dump(backup_payload, f, indent=2)
    print(f"💾 Backed up mon_jin_deku flags to {BACKUP_FILE}")

    # Copy flags from azansalehhh
    # {other-explosion: deny, creeper-explosion: deny, tnt: deny, pvp: deny, pvp-group: NON_OWNERS}
    print("🛡️ Setting flags on 'mon_jin_deku' matching 'azansalehhh'...")
    send_exaroton_command('rg flag -w "world" mon_jin_deku other-explosion deny')
    send_exaroton_command('rg flag -w "world" mon_jin_deku creeper-explosion deny')
    send_exaroton_command('rg flag -w "world" mon_jin_deku tnt deny')
    send_exaroton_command('rg flag -w "world" mon_jin_deku pvp deny')
    send_exaroton_command('rg flag -w "world" mon_jin_deku -g NON_OWNERS pvp deny')

    # Save and reload
    send_exaroton_command("wg save")
    send_exaroton_command("rg reload")

    # Sync back
    sync_pull_regions()
    print("✅ Finished copying flags successfully!")

if __name__ == "__main__":
    main()
