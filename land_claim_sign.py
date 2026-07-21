#!/usr/bin/env python3
"""
Land Ownership Custom Sign Claiming System
------------------------------------------
Monitors Shopkeepers trade log for purchases of Land Ownership item.
When a Land Ownership purchase is detected or a custom Claim Sign is placed,
this system ensures a region is defined around the placed sign as center,
avoiding overlaps with non-global regions, and drawing a smooth cement outline.

Usage:
  python3 land_claim_sign.py [--loop]
"""

import os
import sys
import json
import time
import sqlite3
import subprocess
def load_regions():
    pull_file(REGIONS_FILE, REGIONS_FILE)
    if not os.path.exists(REGIONS_FILE):
        return {}
    
    import re
    regions = {}
    current_region = None
    with open(REGIONS_FILE, "r") as f:
        for line in f:
            reg_match = re.match(r"^ {4}([a-zA-Z0-9_\-]+):", line)
            if reg_match:
                current_region = reg_match.group(1)
                regions[current_region] = {"min": {}, "max": {}}
                continue
            if current_region:
                if "min:" in line:
                    m = re.search(r"x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)", line)
                    if m:
                        regions[current_region]["min"] = {"x": int(m.group(1)), "y": int(m.group(2)), "z": int(m.group(3))}
                elif "max:" in line:
                    m = re.search(r"x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)", line)
                    if m:
                        regions[current_region]["max"] = {"x": int(m.group(1)), "y": int(m.group(2)), "z": int(m.group(3))}
    return regions

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
PROCESSED_FILE = "Shopkeepers/processed_claims.json"
REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"

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
            print(f"✅ Console: {cmd}")
            return True
        else:
            print(f"❌ Console error: {data.get('error')} | Command: {cmd}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

def pull_file(remote_path, local_path):
    pull_cmd = [sys.executable, "sync.py", "pull", remote_path]
    subprocess.run(pull_cmd, capture_output=True)

def check_overlap(min_x, min_z, max_x, max_z, regions, ignore_region=None):
    """
    Checks if candidate region [min_x..max_x, min_z..max_z] overlaps with any
    existing non-global region.
    Returns overlapping region name if overlap found, else None.
    """
    for reg_name, reg_data in regions.items():
        if reg_name == "__global__" or reg_name == ignore_region:
            continue
        rmin = reg_data.get("min", {})
        rmax = reg_data.get("max", {})
        if not rmin or not rmax:
            continue
        
        # Check standard AABB bounding box collision in X/Z
        ex_min_x, ex_max_x = rmin.get("x", 0), rmax.get("x", 0)
        ex_min_z, ex_max_z = rmin.get("z", 0), rmax.get("z", 0)

        # Overlap condition:
        # min1 <= max2 and max1 >= min2
        if (min_x <= ex_max_x and max_x >= ex_min_x) and (min_z <= ex_max_z and max_z >= ex_min_z):
            return reg_name
    return None

def create_land_claim(player_name, center_x, center_y, center_z, radius=12, height_below=5, height_above=10, world="world"):
    """
    Creates a region centered at (center_x, center_z) with radius.
    Total size = (2*radius + 1) x (2*radius + 1). (default radius=12 -> 25x25 plot).
    Max height is capped at 10 blocks above sign level (center_y + 10).
    Checks overlap with non-global regions before creating.
    Draws smooth cement (gray_concrete) border strictly on the floor level.
    """
    regions = load_regions()
    
    cand_min_x = center_x - radius
    cand_max_x = center_x + radius
    cand_min_z = center_z - radius
    cand_max_z = center_z + radius
    cand_min_y = max(-64, center_y - height_below)
    cand_max_y = min(319, center_y + height_above) # Max height is 10 blocks above sign

    # Sanitize region name for player
    clean_player = player_name.lower().replace(".", "").strip()
    region_name = f"{clean_player}_land"
    
    # Check if region already exists or if overlapping
    overlapping = check_overlap(cand_min_x, cand_min_z, cand_max_x, cand_max_z, regions, ignore_region=region_name)
    if overlapping:
        print(f"❌ Cannot create claim for {player_name}: overlaps with existing region '{overlapping}'!")
        send_exaroton_command(f'say §c[Land Claim] Failed for {player_name}: overlaps with existing region ({overlapping})!')
        return False

    print(f"✨ Creating Land Claim '{region_name}' for {player_name} centered at ({center_x}, {center_y}, {center_z})...")
    
    # 1. Select region & define via WorldEdit / WorldGuard
    send_exaroton_command(f"//pos1 {cand_min_x},{cand_min_y},{cand_min_z} -w {world}")
    send_exaroton_command(f"//pos2 {cand_max_x},{cand_max_y},{cand_max_z} -w {world}")
    
    # Define or redefine WorldGuard region
    send_exaroton_command(f"rg define -w {world} {region_name} {player_name}")
    
    # Add player as owner
    send_exaroton_command(f"rg addowner -w {world} {region_name} {player_name}")
    
    # 2. Draw smooth cement outline border on the floor only (1 block high flat border flush with the ground floor)
    floor_y = center_y - 1
    send_exaroton_command(f"//pos1 {cand_min_x},{floor_y},{cand_min_z} -w {world}")
    send_exaroton_command(f"//pos2 {cand_max_x},{floor_y},{cand_max_z} -w {world}")
    # Replace outer perimeter floor blocks with gray concrete
    send_exaroton_command(f"//walls gray_concrete")
    
    # 3. Disappear/remove the claim sign at center_x, center_y, center_z so it cannot be reused
    send_exaroton_command(f"setblock {center_x} {center_y} {center_z} air")
    
    # Save WorldGuard & WorldEdit changes to disk and server memory
    send_exaroton_command(f"rg save -w {world}")
    send_exaroton_command("wg save")
    send_exaroton_command("rg reload")
    
    real_name = PLAYER_MAP.get(player_name, player_name)
    send_exaroton_command(f'say §6[Land Claim] §a{real_name} §ehas placed a Land Ownership Sign! Claimed §b{cand_max_x - cand_min_x + 1}x{cand_max_z - cand_min_z + 1} §earea (Max Height: 10 blocks) with floor outline!')
    return True

def undo_land_claim(player_name, world="world"):
    """
    Undoes a land claim for a player: removes WorldGuard region and reverts floor blocks if needed.
    """
    clean_player = player_name.lower().replace(".", "").strip()
    region_name = f"{clean_player}_land"
    
    print(f"🔄 Undoing Land Claim for '{region_name}'...")
    
    # 1. Delete region from WorldGuard
    send_exaroton_command(f"rg delete -w {world} {region_name}")
    
    # 2. Always save WorldGuard configuration immediately
    send_exaroton_command(f"rg save -w {world}")
    send_exaroton_command("wg save")
    send_exaroton_command("rg reload")
    
    real_name = PLAYER_MAP.get(player_name, player_name)
    send_exaroton_command(f'say §c[Land Claim] §eLand claim for §a{real_name} §ehas been undone and region removed.')
    return True

def give_custom_claim_sign(player_name):
    """
    Removes the purchased certificate book from player inventory, gives the custom claim sign,
    and sends detailed instructions in chat.
    """
    # Remove any written_book / certificate book from player inventory
    send_exaroton_command(f'clear {player_name} written_book 1')
    send_exaroton_command(f'clear {player_name} book 1')

    # Give custom Land Claim Sign
    sign_item = f'oak_sign[item_name=\'"§6Land Claim Sign"\',lore=[\'"§7Place this sign to claim your land!"\',\'"§7Creates a 25x25 protected area centered on sign."\']]'
    cmd = f'give {player_name} {sign_item} 1'
    print(f"🎁 Giving custom Land Claim Sign to {player_name} (replaced certificate book)...")
    send_exaroton_command(cmd)

    real_name = PLAYER_MAP.get(player_name, player_name)
    # Direct tellraw instruction message to player
    tell_cmd = (
        f'tellraw {player_name} ['
        f'{{"text":"\\n§6§l=== 📜 LAND CLAIM SIGN INSTRUCTIONS ===\\n","bold":true}},'
        f'{{"text":"§eCongratulations §a{real_name}§e! You received a §6Land Claim Sign§e.\\n"}},'
        f'{{"text":"§b1. §fPlace the sign in the center of where you want your plot.\\n"}},'
        f'{{"text":"§b2. §fIt automatically creates a §a25x25 §fprotected area around it.\\n"}},'
        f'{{"text":"§b3. §fMax height protection is §a10 blocks §fabove the sign.\\n"}},'
        f'{{"text":"§b4. §fA §7smooth cement outline §fwill mark your floor border!\\n"}},'
        f'{{"text":"§cNote: Make sure not to place it inside someone else\'s claim!\\n"}},'
        f'{{"text":"§6§l========================================\\n"}}'
        f']'
    )
    send_exaroton_command(tell_cmd)
    
    # Public announcement broadcast
    send_exaroton_command(f'say §6[Land Claim] §a{real_name} §epurchased a §6Land Claim Sign§e! Check your inventory and chat for placement instructions.')

def audit_tradelog_for_land():
    """
    Checks trade log for Land Ownership purchases and issues custom claim signs.
    """
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
                trade_key = f"{timestamp}_{player_name}_{result_type}_{hash(metadata)}"

                if trade_key in processed:
                    continue

                metadata_lower = metadata.lower()
                # Check for Land / Plot / Claim keywords in trade result item
                if "land" in metadata_lower or "claim" in metadata_lower or "ownership" in metadata_lower or "plot" in metadata_lower or "expansion" in metadata_lower:
                    print(f"🛒 Land purchase detected for player: {player_name}")
                    give_custom_claim_sign(player_name)
                    
                    processed.add(trade_key)
                    with open(PROCESSED_FILE, "w") as f:
                        json.dump(list(processed), f)

    except Exception as e:
        print(f"Trade audit error: {e}")
    finally:
        conn.close()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "claim":
        # Direct CLI mode: python3 land_claim_sign.py claim <player> <x> <y> <z> [radius]
        if len(sys.argv) >= 5:
            player = sys.argv[2]
            x, y, z = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
            radius = int(sys.argv[6]) if len(sys.argv) >= 7 else 12
            create_land_claim(player, x, y, z, radius=radius)
        else:
            print("Usage: python3 land_claim_sign.py claim <player> <x> <y> <z> [radius]")
        return

    if len(sys.argv) > 1 and sys.argv[1] == "undo":
        # Undo CLI mode: python3 land_claim_sign.py undo <player>
        if len(sys.argv) >= 3:
            undo_land_claim(sys.argv[2])
        else:
            print("Usage: python3 land_claim_sign.py undo <player>")
        return

    if len(sys.argv) > 1 and sys.argv[1] == "give":
        if len(sys.argv) >= 3:
            give_custom_claim_sign(sys.argv[2])
        return

    loop_mode = "--loop" in sys.argv or "-l" in sys.argv
    pull_file(DB_PATH, DB_PATH)
    audit_tradelog_for_land()
    print("✅ Land Claim Sign audit completed.")

if __name__ == "__main__":
    main()
