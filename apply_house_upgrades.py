#!/usr/bin/env python3
"""
Automated House Upgrade Tracker & Region Flag Applicator
--------------------------------------------------------
1. Downloads the SQLite trade log from Exaroton (`Shopkeepers/trade-logs/trades.db`).
2. Scans for purchases of TNT, Creeper, PvP, Mob Spawn, and Fire Protection certificates.
3. Maps player Bedrock / Java usernames to their corresponding WorldGuard regions.
4. Executes `/rg flag <region> <flag> deny` on the Exaroton server via API.
5. Broadcasts public chat message (`/say ...`) so everyone sees who got which protection.
"""

import os
import sys
import json
import sqlite3
import subprocess
import time
import re

# Load environment
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
DB_PATH = "Shopkeepers/trade-logs/trades.db"
PROCESSED_FILE = "Shopkeepers/processed_trades.json"

# Player Mapping Reference
PLAYER_MAP = {
    ".mustafahacker67": "mustafa",
    "mustafahacker67": "mustafa",
    ".HastyBag7675": "muhammad saleh",
    "HastyBag7675": "muhammad saleh",
    ".WiryCircle3938": "omer saleh",
    "WiryCircle3938": "omer saleh",
    "hanansaleh": "hanan saleh",
    "manansaleh2007": "manan saleh",
    "NightmareDady": "rayan saleh",
    "nightmaredady": "rayan saleh",
    ".AzanSaleh": "azan saleh",
    "AzanSaleh": "azan saleh",
    "azansalehhh": "azan saleh"
}

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

# Certificate Name Keywords to (WorldGuard Flag, Display Name)
CERT_FLAG_MAP = {
    "tnt protection": ("tnt", "TNT Protection"),
    "creeper": ("other-explosion", "Creeper/Explosion Protection"),
    "pvp protection": ("pvp", "PvP Protection"),
    "mob spawn": ("mob-spawning", "Mob Spawn Protection"),
    "fire spread": ("fire-spread", "Fire Spread Protection")
}

def get_region_for_player(player_name):
    if player_name in PLAYER_REGION_MAP:
        return PLAYER_REGION_MAP[player_name]
    clean = player_name.lower().replace(".", "")
    if clean in PLAYER_REGION_MAP:
        return PLAYER_REGION_MAP[clean]
    return clean

def get_region_flags(regions_file="WorldGuard/worlds/world/regions.yml"):
    pull_cmd = [sys.executable, "sync.py", "pull", regions_file]
    subprocess.run(pull_cmd, capture_output=True)

    region_flags = {}
    if not os.path.exists(regions_file):
        return region_flags

    current_region = None
    with open(regions_file, "r") as f:
        for line in f:
            region_match = re.match(r"^ {4}([a-zA-Z0-9_\-]+):", line)
            if region_match:
                current_region = region_match.group(1)
                if current_region not in region_flags:
                    region_flags[current_region] = {}
                continue

            if current_region and "flags:" in line:
                flags_content = line.split("flags:", 1)[1].strip()
                if flags_content.startswith("{") and flags_content.endswith("}"):
                    inner = flags_content[1:-1].strip()
                    if inner:
                        pairs = inner.split(",")
                        for pair in pairs:
                            if ":" in pair:
                                k, v = pair.split(":", 1)
                                region_flags[current_region][k.strip()] = v.strip()
    return region_flags

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
    if "success" in res.stdout:
        print(f"✅ Executed: {cmd}")
    else:
        print(f"❌ Failed: {cmd} | Response: {res.stdout}")

def broadcast_upgrade_in_chat(player_name, upgrade_title):
    # Broadcasts public chat message to ALL players
    display_name = PLAYER_MAP.get(player_name, player_name)
    msg_cmd = f'say §6[Upgrade] §a{display_name} §eunlocked §b{upgrade_title} §efor their house!'
    send_exaroton_command(msg_cmd)

def sync_tradelog():
    pull_cmd = [sys.executable, "sync.py", "pull", DB_PATH]
    subprocess.run(pull_cmd, capture_output=True)

def audit_and_apply_upgrades():
    if not os.path.exists(DB_PATH):
        return

    processed = set()
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, "r") as f:
                processed = set(json.load(f))
        except Exception:
            processed = set()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        if "trade" in tables:
            cursor.execute("SELECT timestamp, player_name, result_item_type, result_item_metadata FROM trade")
            rows = cursor.fetchall()
            for r in rows:
                timestamp, player_name, result_type, metadata = str(r[0]), str(r[1]), str(r[2]), str(r[3] or "")
                trade_key = f"{timestamp}_{player_name}_{result_type}"

                if trade_key in processed:
                    continue

                metadata_lower = metadata.lower()
                for keyword, (flag, label) in CERT_FLAG_MAP.items():
                    if keyword in metadata_lower or (result_type == "WRITTEN_BOOK" and not metadata):
                        region_name = get_region_for_player(player_name)

                        print(f"🎯 Processing new upgrade {label} for {player_name} -> Region: {region_name}")

                        # 1. Apply WorldGuard flag (for PvP, allow owners to defend against non-owners)
                        if flag == "pvp":
                            flag_cmd = f"rg flag -w \"world\" {region_name} pvp -g non_owners deny"
                        else:
                            flag_cmd = f"rg flag -w \"world\" {region_name} {flag} deny"
                        send_exaroton_command(flag_cmd)

                        # 2. Save WorldGuard data to disk
                        send_exaroton_command("wg save")

                        # 3. Broadcast in public chat to everyone (ONCE)
                        broadcast_upgrade_in_chat(player_name, label)

                        # 4. Record as processed immediately
                        processed.add(trade_key)
                        with open(PROCESSED_FILE, "w") as f:
                            json.dump(list(processed), f)
                        break

    except Exception as e:
        print(f"Trade audit note: {e}")
    finally:
        conn.close()

def main():
    loop_mode = "--loop" in sys.argv or "-l" in sys.argv or os.environ.get("LOOP_MODE") == "true"
    duration = int(os.environ.get("LOOP_DURATION", "270")) if loop_mode else 0
    poll_interval = int(os.environ.get("POLL_INTERVAL", "2"))

    if loop_mode:
        print(f"🔄 Upgrade checker running (polling every {poll_interval}s for {duration}s)...")
        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                sync_tradelog()
                audit_and_apply_upgrades()
            except Exception as e:
                print(f"Error during check iteration: {e}")
            time.sleep(poll_interval)
    else:
        sync_tradelog()
        audit_and_apply_upgrades()

if __name__ == "__main__":
    main()
