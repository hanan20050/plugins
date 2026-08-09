#!/usr/bin/env python3
"""
Full Audit System for Minecraft Server Plugins & Economy
Audits item flow ("what came from where and went where"), currency provenance,
recipe glitches, anti-exploit threshold violations, WorldGuard region protections,
and player identity/UUID mappings.
"""

import os
import sys
import json
import sqlite3
import re
from datetime import datetime

# User Rules & Player Mappings
PLAYER_MAP = {
    ".mustafahacker67": "mustafa",
    "mustafahacker67": "mustafa",
    ".HastyBag7675": "muhammad saleh",
    "HastyBag7675": "muhammad saleh",
    ".WiryCircle3938": "omer saleh",
    "WiryCircle3938": "omer saleh",
    "hanansaleh": "hanan saleh",
    "manan2007": "manan saleh",
    "manan200502007": "manan saleh",
    ".manan2007": "manan saleh",
    "NightmareDady": "rayan saleh",
    ".AzanSaleh": "azan saleh",
    "azansalehhh": "azan saleh",
    "AzanSaleh": "azan saleh"
}

# Base Currency Ratios in Emeralds
CURRENCY_RATES = {
    "minecraft:emerald": 1,
    "minecraft:emerald_block": 9,
    "minecraft:netherite_ingot": 64,
    "minecraft:netherite_block": 576
}

# Unstackable item types (max stack 1)
UNSTACKABLE_KEYWORDS = [
    "_sword", "_pickaxe", "_axe", "_shovel", "_hoe",
    "_helmet", "_chestplate", "_leggings", "_boots",
    "bow", "crossbow", "trident", "shield", "elytra",
    "shears", "flint_and_steel", "fishing_rod",
    "saddle", "horse_armor", "written_book", "enchanted_book",
    "totem_of_undying", "shulker_box"
]

SIXTEEN_STACKABLE = [
    "ender_pearl", "egg", "snowball", "bucket",
    "honey_bottle", "sign", "banner"
]

def resolve_player_name(raw_name):
    if not raw_name:
        return "Unknown Player"
    clean_name = str(raw_name).strip()
    if clean_name in PLAYER_MAP:
        return PLAYER_MAP[clean_name]
    for key, val in PLAYER_MAP.items():
        if clean_name.lower() == key.lower():
            return val
    return clean_name

def is_unstackable(item_id):
    if not item_id:
        return False
    item = str(item_id).lower().replace("minecraft:", "")
    for kw in UNSTACKABLE_KEYWORDS:
        if kw in item:
            return True
    return False

def is_16_stackable(item_id):
    if not item_id:
        return False
    item = str(item_id).lower().replace("minecraft:", "")
    for kw in SIXTEEN_STACKABLE:
        if kw in item:
            return True
    return False

def get_max_stack(item_id):
    if is_unstackable(item_id):
        return 1
    if is_16_stackable(item_id):
        return 16
    return 64

def calculate_item_emerald_value(item_id, count):
    if not item_id:
        return 0
    item = str(item_id).lower().strip()
    if item in CURRENCY_RATES:
        return CURRENCY_RATES[item] * (count or 0)
    return 0

def parse_save_yml(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r") as f:
        content = f.read()

    shops_raw = re.split(r'\n(\'?\d+\'?):\n', content)
    shops = {}

    for i in range(1, len(shops_raw), 2):
        shop_id = shops_raw[i].strip("'")
        shop_body = shops_raw[i+1]
        
        name_m = re.search(r'name:\s*[\'\"]?(.*?)[\'\"]?\n', shop_body)
        shop_name = name_m.group(1) if name_m else f"Shop #{shop_id}"

        type_m = re.search(r'type:\s*[\'\"]?(.*?)[\'\"]?\n', shop_body)
        shop_type = type_m.group(1) if type_m else "admin"

        x_m = re.search(r'x:\s*(-?\d+)', shop_body)
        y_m = re.search(r'y:\s*(-?\d+)', shop_body)
        z_m = re.search(r'z:\s*(-?\d+)', shop_body)
        world_m = re.search(r'world:\s*(\w+)', shop_body)

        x = int(x_m.group(1)) if x_m else 0
        y = int(y_m.group(1)) if y_m else 0
        z = int(z_m.group(1)) if z_m else 0
        world = world_m.group(1) if world_m else "world"

        recipes_raw = re.split(r'\n\s{4}(\'\d+\'|\d+):\n', shop_body)
        recipes = []

        for r_idx in range(1, len(recipes_raw), 2):
            rec_id = recipes_raw[r_idx].strip("'")
            rec_body = recipes_raw[r_idx+1]

            res_m = re.search(r'resultItem:.*?\n\s+DataVersion:.*?\n\s+id:\s*(minecraft:\w+)\n\s+count:\s*(\d+)', rec_body, re.DOTALL)
            i1_m = re.search(r'item1:.*?\n\s+DataVersion:.*?\n\s+id:\s*(minecraft:\w+)\n\s+count:\s*(\d+)', rec_body, re.DOTALL)
            i2_m = re.search(r'item2:.*?\n\s+DataVersion:.*?\n\s+id:\s*(minecraft:\w+)\n\s+count:\s*(\d+)', rec_body, re.DOTALL)

            res_id = res_m.group(1) if res_m else ""
            res_cnt = int(res_m.group(2)) if res_m else 0

            i1_id = i1_m.group(1) if i1_m else ""
            i1_cnt = int(i1_m.group(2)) if i1_m else 0

            i2_id = i2_m.group(1) if i2_m else ""
            i2_cnt = int(i2_m.group(2)) if i2_m else 0

            recipes.append({
                "recipe_id": rec_id,
                "item1_id": i1_id,
                "item1_count": i1_cnt,
                "item2_id": i2_id,
                "item2_count": i2_cnt,
                "result_id": res_id,
                "result_count": res_cnt
            })

        shops[shop_id] = {
            "id": shop_id,
            "name": shop_name,
            "type": shop_type,
            "world": world,
            "x": x, "y": y, "z": z,
            "recipes": recipes
        }

    return shops

def audit_trade_database(db_paths):
    player_stats = {}
    shop_stats = {}
    anomalies = []
    total_records_processed = 0

    for db_path in db_paths:
        if not os.path.exists(db_path):
            continue

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM trade ORDER BY timestamp ASC;")
        rows = cursor.fetchall()
        
        cursor.execute("PRAGMA table_info(trade);")
        cols = [c[1] for c in cursor.fetchall()]
        conn.close()

        col_idx = {name: idx for idx, name in enumerate(cols)}

        for row in rows:
            total_records_processed += 1
            ts = row[col_idx["timestamp"]]
            p_uuid = row[col_idx["player_uuid"]]
            p_name = row[col_idx["player_name"]]
            real_player = resolve_player_name(p_name)

            s_uuid = row[col_idx["shop_uuid"]]
            s_type = row[col_idx["shop_type"]]
            s_world = row[col_idx.get("shop_world")] or "world"
            s_x = row[col_idx["shop_x"]]
            s_y = row[col_idx["shop_y"]]
            s_z = row[col_idx["shop_z"]]
            s_owner = row[col_idx.get("shop_owner_name")] or "Admin"

            i1_type = row[col_idx["item_1_type"]] or ""
            i1_amt = row[col_idx["item_1_amount"]] or 0

            i2_type = row[col_idx.get("item_2_type")] or ""
            i2_amt = row[col_idx.get("item_2_amount")] or 0

            res_type = row[col_idx["result_item_type"]] or ""
            res_amt = row[col_idx["result_item_amount"]] or 0
            t_count = row[col_idx["trade_count"]] or 1

            # Amounts for this execution
            total_i1 = i1_amt * t_count
            total_i2 = i2_amt * t_count
            total_res = res_amt * t_count

            # Emerald value calculations
            i1_val = calculate_item_emerald_value(i1_type, total_i1)
            i2_val = calculate_item_emerald_value(i2_type, total_i2)
            res_val = calculate_item_emerald_value(res_type, total_res)

            net_val_gained = res_val - (i1_val + i2_val)

            # Player stats accumulation
            if real_player not in player_stats:
                player_stats[real_player] = {
                    "raw_names": set(),
                    "uuids": set(),
                    "total_trades": 0,
                    "items_given": {},
                    "items_received": {},
                    "emeralds_spent": 0,
                    "emeralds_gained": 0,
                    "net_emerald_balance": 0,
                    "first_trade": ts,
                    "last_trade": ts,
                    "shops_used": set()
                }

            ps = player_stats[real_player]
            ps["raw_names"].add(p_name)
            ps["uuids"].add(p_uuid)
            ps["total_trades"] += t_count
            ps["last_trade"] = ts
            ps["shops_used"].add(f"({s_x},{s_y},{s_z})")

            # Items given
            if i1_type:
                ps["items_given"][i1_type] = ps["items_given"].get(i1_type, 0) + total_i1
            if i2_type:
                ps["items_given"][i2_type] = ps["items_given"].get(i2_type, 0) + total_i2

            # Items received
            if res_type:
                ps["items_received"][res_type] = ps["items_received"].get(res_type, 0) + total_res

            ps["emeralds_spent"] += (i1_val + i2_val)
            ps["emeralds_gained"] += res_val
            ps["net_emerald_balance"] += net_val_gained

            # Shop stats accumulation
            shop_key = f"Shop@({s_x},{s_y},{s_z})"
            if shop_key not in shop_stats:
                shop_stats[shop_key] = {
                    "coords": (s_x, s_y, s_z),
                    "world": s_world,
                    "total_trades": 0,
                    "items_received": {},
                    "items_dispensed": {},
                    "players_serviced": set()
                }

            ss = shop_stats[shop_key]
            ss["total_trades"] += t_count
            ss["players_serviced"].add(real_player)
            if i1_type:
                ss["items_received"][i1_type] = ss["items_received"].get(i1_type, 0) + total_i1
            if i2_type:
                ss["items_received"][i2_type] = ss["items_received"].get(i2_type, 0) + total_i2
            if res_type:
                ss["items_dispensed"][res_type] = ss["items_dispensed"].get(res_type, 0) + total_res

            # Anomaly Checks
            # 1. Unstackable count anomaly
            if is_unstackable(res_type) and res_amt > 1:
                anomalies.append({
                    "type": "LOGGED_UNSTACKABLE_OVERCOUNT",
                    "severity": "HIGH",
                    "player": real_player,
                    "timestamp": ts,
                    "details": f"Player {p_name} received {res_amt}x unstackable item '{res_type}' per trade execution at shop ({s_x},{s_y},{s_z}) [Source DB: {os.path.basename(db_path)}]."
                })
            if is_unstackable(i1_type) and i1_amt > 1:
                anomalies.append({
                    "type": "LOGGED_UNSTACKABLE_OVERCOUNT",
                    "severity": "HIGH",
                    "player": real_player,
                    "timestamp": ts,
                    "details": f"Player {p_name} provided {i1_amt}x unstackable item '{i1_type}' per trade execution at shop ({s_x},{s_y},{s_z}) [Source DB: {os.path.basename(db_path)}]."
                })

            # 2. High volume item dumping anomaly (>50 items sold in single trade)
            if res_type in ["minecraft:emerald", "minecraft:emerald_block"] and total_i1 >= 50:
                anomalies.append({
                    "type": "HIGH_VOLUME_ITEM_DUMP",
                    "severity": "MEDIUM",
                    "player": real_player,
                    "timestamp": ts,
                    "details": f"Player {p_name} dumped {total_i1}x '{i1_type}' to shop at ({s_x},{s_y},{s_z}) in single transaction."
                })

            # 3. Identity Check: Bedrock username missing '.' prefix
            if not p_name.startswith(".") and real_player in [".mustafahacker67", ".HastyBag7675", ".WiryCircle3938", ".AzanSaleh"]:
                anomalies.append({
                    "type": "UNMAPPED_BEDROCK_PREFIX",
                    "severity": "LOW",
                    "player": real_player,
                    "timestamp": ts,
                    "details": f"Trade logged with raw username '{p_name}' without Bedrock '.' prefix."
                })

    for p in player_stats:
        player_stats[p]["raw_names"] = list(player_stats[p]["raw_names"])
        player_stats[p]["uuids"] = list(player_stats[p]["uuids"])
        player_stats[p]["shops_used"] = list(player_stats[p]["shops_used"])

    for s in shop_stats:
        shop_stats[s]["players_serviced"] = list(shop_stats[s]["players_serviced"])

    return player_stats, shop_stats, anomalies, total_records_processed

def audit_save_yml_recipes(shops):
    anomalies = []
    
    for s_id, s_data in shops.items():
        s_name = s_data["name"]
        recipes = s_data["recipes"]
        seen_recipes = set()

        for rec in recipes:
            r_id = rec["recipe_id"]
            i1_id = rec["item1_id"]
            i1_cnt = rec["item1_count"]
            i2_id = rec["item2_id"]
            i2_cnt = rec["item2_count"]
            res_id = rec["result_id"]
            res_cnt = rec["result_count"]

            # 1. Unstackable Cap Audit
            if is_unstackable(res_id) and res_cnt > 1:
                anomalies.append({
                    "type": "RECIPE_UNSTACKABLE_OVERCAP",
                    "severity": "HIGH",
                    "shop_id": s_id,
                    "shop_name": s_name,
                    "recipe_id": r_id,
                    "details": f"Shop #{s_id} ({s_name}) recipe #{r_id} gives {res_cnt}x unstackable item '{res_id}' (Max allowed: 1)."
                })
            if is_unstackable(i1_id) and i1_cnt > 1:
                anomalies.append({
                    "type": "RECIPE_UNSTACKABLE_OVERCAP",
                    "severity": "HIGH",
                    "shop_id": s_id,
                    "shop_name": s_name,
                    "recipe_id": r_id,
                    "details": f"Shop #{s_id} ({s_name}) recipe #{r_id} requires {i1_cnt}x unstackable item '{i1_id}' (Max allowed: 1)."
                })

            # 2. Money Exchange Cleanliness Audit (Rule: Exchange trades strictly in Shop ID 5)
            is_currency_i1 = i1_id in CURRENCY_RATES
            is_currency_res = res_id in CURRENCY_RATES
            
            if is_currency_i1 and is_currency_res:
                if s_id != "5":
                    anomalies.append({
                        "type": "MISPLACED_EXCHANGE_TRADE",
                        "severity": "CRITICAL",
                        "shop_id": s_id,
                        "shop_name": s_name,
                        "recipe_id": r_id,
                        "details": f"Exchange trade ({i1_cnt}x {i1_id} -> {res_cnt}x {res_id}) exists in Shop #{s_id} ('{s_name}'). Exchange trades must strictly exist ONLY in Shop ID 5."
                    })
                
                # Check fixed exchange rate compliance
                i1_val = CURRENCY_RATES[i1_id] * i1_cnt
                res_val = CURRENCY_RATES[res_id] * res_cnt
                if i1_val != res_val:
                    anomalies.append({
                        "type": "EXCHANGE_RATE_DEVIATION",
                        "severity": "CRITICAL",
                        "shop_id": s_id,
                        "shop_name": s_name,
                        "recipe_id": r_id,
                        "details": f"Exchange rate deviation in Shop #{s_id}: {i1_cnt}x {i1_id} (val: {i1_val}) -> {res_cnt}x {res_id} (val: {res_val}). Fixed exchange rates must never be altered!"
                    })

            # 3. Duplicate Recipe Audit
            rec_sig = f"{i1_id}:{i1_cnt}|{i2_id}:{i2_cnt}->{res_id}:{res_cnt}"
            if rec_sig in seen_recipes:
                anomalies.append({
                    "type": "DUPLICATE_RECIPE",
                    "severity": "LOW",
                    "shop_id": s_id,
                    "shop_name": s_name,
                    "recipe_id": r_id,
                    "details": f"Duplicate trade recipe found in Shop #{s_id} ({s_name}): {rec_sig}"
                })
            else:
                seen_recipes.add(rec_sig)

    return anomalies

def parse_worldguard_regions(base_dir="WorldGuard/worlds"):
    if not os.path.exists(base_dir):
        return {}, []

    region_data = {}
    anomalies = []

    for world_folder in os.listdir(base_dir):
        world_path = os.path.join(base_dir, world_folder, "regions.yml")
        if not os.path.exists(world_path):
            continue

        with open(world_path, "r") as f:
            content = f.read()

        regions_raw = re.split(r'\n\s{4}(\w+):\n', content)
        for i in range(1, len(regions_raw), 2):
            reg_name = regions_raw[i]
            reg_body = regions_raw[i+1]

            min_m = re.search(r'min:\s*\{x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)\}', reg_body)
            max_m = re.search(r'max:\s*\{x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)\}', reg_body)

            min_x = int(min_m.group(1)) if min_m else 0
            min_y = int(min_m.group(2)) if min_m else 0
            min_z = int(min_m.group(3)) if min_m else 0

            max_x = int(max_m.group(1)) if max_m else 0
            max_y = int(max_m.group(2)) if max_m else 0
            max_z = int(max_m.group(3)) if max_m else 0

            width = (max_x - min_x) + 1
            length = (max_z - min_z) + 1

            if max(width, length) <= 15:
                category = "Starter / Base Plot"
            elif max(width, length) <= 25:
                category = "Small Plot"
            elif max(width, length) <= 50:
                category = "Normal Plot"
            else:
                category = "Big Plot"

            uuids_list = re.findall(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', reg_body)

            if "owners:" in reg_body and "unique-ids:" not in reg_body and reg_name != "__global__":
                anomalies.append({
                    "type": "REGION_MISSING_UUID_OWNER",
                    "severity": "HIGH",
                    "world": world_folder,
                    "region": reg_name,
                    "details": f"Region '{reg_name}' in world '{world_folder}' defines owners but is missing UUIDs under 'owners.unique-ids'."
                })

            flags_m = re.search(r'flags:\s*\n((\s+[\w-]+:\s*[^\n]+\n)+)', reg_body)
            flags = {}
            if flags_m:
                flag_block = flags_m.group(1)
                for line in flag_block.splitlines():
                    parts = line.strip().split(":", 1)
                    if len(parts) == 2:
                        flags[parts[0].strip()] = parts[1].strip()

            region_data[f"{world_folder}/{reg_name}"] = {
                "world": world_folder,
                "region": reg_name,
                "min": (min_x, min_y, min_z),
                "max": (max_x, max_y, max_z),
                "width": width,
                "length": length,
                "category": category,
                "uuids": uuids_list,
                "flags": flags
            }

    return region_data, anomalies

def write_markdown_artifact(player_stats, shop_stats, shops, regions, anomalies, total_records):
    artifact_dir = "/Users/hanansaleh/.gemini/antigravity-ide/brain/61452776-0c51-498e-bf1b-cc281fa7c163"
    artifact_path = os.path.join(artifact_dir, "audit_report.md")
    
    os.makedirs(artifact_dir, exist_ok=True)
    
    lines = []
    lines.append("# Exaroton Minecraft Server Full Economy & Data Audit Report")
    lines.append(f"**Audit Execution Time:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n")
    
    lines.append("## Executive Summary")
    lines.append(f"- **Total Trade Database Records Processed:** `{total_records}`")
    lines.append(f"- **Unique Players Audited:** `{len(player_stats)}`")
    lines.append(f"- **Active Shopkeepers Audited:** `{len(shops)}`")
    lines.append(f"- **WorldGuard Regions Audited:** `{len(regions)}`")
    lines.append(f"- **Total Anomalies Detected:** `{len(anomalies)}`\n")

    lines.append("## 1. Player Item & Currency Flow Matrix")
    lines.append("Below is the complete audit breakdown of **what came from where and went where** for every active player:\n")

    for player, stats in player_stats.items():
        lines.append(f"### Player: `{player.upper()}`")
        lines.append(f"- **Known Usernames / Aliases:** `{', '.join(stats['raw_names'])}`")
        lines.append(f"- **Recorded UUIDs:** `{', '.join(stats['uuids'])}`")
        lines.append(f"- **Total Completed Trade Operations:** `{stats['total_trades']}`")
        lines.append(f"- **First Activity:** `{stats['first_trade']}` | **Last Activity:** `{stats['last_trade']}`")
        lines.append(f"- **Financial Overview (Emerald Value):**")
        lines.append(f"  - Total Emerald Value Spent: `{stats['emeralds_spent']}`")
        lines.append(f"  - Total Emerald Value Gained: `{stats['emeralds_gained']}`")
        lines.append(f"  - **Net Emerald Balance Change:** `{stats['net_emerald_balance']}`")
        
        lines.append("\n#### Items Provided (Given by Player to Shops)")
        lines.append("| Item ID | Total Quantity Provided |")
        lines.append("|---|---|")
        for itype, icnt in sorted(stats["items_given"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| `{itype}` | {icnt} |")

        lines.append("\n#### Items Received (Obtained by Player from Shops)")
        lines.append("| Item ID | Total Quantity Received |")
        lines.append("|---|---|")
        for itype, icnt in sorted(stats["items_received"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| `{itype}` | {icnt} |")
        lines.append("\n---\n")

    lines.append("## 2. Shopkeeper Provenance & Volume Analysis")
    lines.append("| Shop Coordinates | World | Total Trades | Unique Customers | Top Dispensed Item |")
    lines.append("|---|---|---|---|---|")
    for s_key, s_data in shop_stats.items():
        coords = f"{s_data['coords'][0]}, {s_data['coords'][1]}, {s_data['coords'][2]}"
        world = s_data['world']
        trades = s_data['total_trades']
        cust_cnt = len(s_data['players_serviced'])
        top_item = max(s_data['items_dispensed'].items(), key=lambda x: x[1])[0] if s_data['items_dispensed'] else "N/A"
        lines.append(f"| `{coords}` | `{world}` | {trades} | {cust_cnt} | `{top_item}` |")

    lines.append("\n## 3. Detected Anomalies & Glitch Inventory")
    if not anomalies:
        lines.append("> [!TIP]")
        lines.append("> No critical anomalies or policy violations detected across trade logs, shop recipes, and WorldGuard regions.")
    else:
        lines.append(f"A total of **{len(anomalies)}** anomalies were detected:\n")
        lines.append("| # | Severity | Anomaly Type | Target / Location | Description & Context |")
        lines.append("|---|---|---|---|---|")
        for idx, anom in enumerate(anomalies, start=1):
            sev = anom.get('severity', 'MEDIUM')
            atype = anom.get('type', 'UNKNOWN')
            loc = anom.get('player') or anom.get('shop_id') or anom.get('region') or "Global"
            details = anom.get('details', '')
            lines.append(f"| {idx} | **{sev}** | `{atype}` | `{loc}` | {details} |")

    lines.append("\n## 4. Actionable Recommendations & Fixes")
    lines.append("1. **Currency Exchange Cleanliness**: Keep all currency exchange trades strictly inside Shop ID 5 (`Money Exchange`).")
    lines.append("2. **Stack Size Enforcement**: Ensure unstackable items (weapons, armor, tools, books) are limited to count 1 per trade.")
    lines.append("3. **WorldGuard UUID Integrity**: Verify all player region definitions in `regions.yml` include full UUIDs under `owners.unique-ids`.")

    with open(artifact_path, "w") as f:
        f.write("\n".join(lines))
        
    print(f" -> Artifact written to: file://{artifact_path}")

def main():
    print("==================================================================")
    print("   EXAROTON MINECRAFT SERVER FULL AUDIT & PROVENANCE SYSTEM       ")
    print("==================================================================")
    print(f"Audit Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    db_paths = [
        "Shopkeepers/trade-logs/trades.db",
        "backup_trades_db_hanan_delete.db"
    ]

    # 1. Audit Trade Log Databases
    print("[1/4] Auditing Trade Databases...")
    player_stats, shop_stats, db_anomalies, total_records = audit_trade_database(db_paths)

    print(f" -> Processed {total_records} database records for {len(player_stats)} unique players.")
    print(f" -> Found {len(db_anomalies)} trade log anomalies.")

    # 2. Audit Save YML Recipes
    print("\n[2/4] Auditing Active Shopkeeper Trade Recipes (`save.yml`)...")
    shops = parse_save_yml("Shopkeepers/data/save.yml")
    recipe_anomalies = audit_save_yml_recipes(shops)
    print(f" -> Parsed {len(shops)} shopkeepers with active recipes.")
    print(f" -> Found {len(recipe_anomalies)} recipe configuration anomalies.")

    # 3. Audit WorldGuard Regions
    print("\n[3/4] Auditing WorldGuard Regions & Protection Flags...")
    regions, region_anomalies = parse_worldguard_regions("WorldGuard/worlds")
    print(f" -> Parsed {len(regions)} regions across worlds.")
    print(f" -> Found {len(region_anomalies)} region protection anomalies.")

    all_anomalies = db_anomalies + recipe_anomalies + region_anomalies

    # 4. Generate Artifact
    print("\n[4/4] Generating Audit Artifact Report...")
    write_markdown_artifact(player_stats, shop_stats, shops, regions, all_anomalies, total_records)

    # Save JSON summary
    audit_summary = {
        "timestamp": datetime.now().isoformat(),
        "total_records": total_records,
        "total_players_audited": len(player_stats),
        "total_shops_audited": len(shops),
        "total_regions_audited": len(regions),
        "total_anomalies_detected": len(all_anomalies),
        "player_stats": player_stats,
        "anomalies": all_anomalies
    }

    with open("audit_results.json", "w") as f:
        json.dump(audit_summary, f, indent=2)

    print("\n==================================================================")
    print("                      AUDIT EXECUTION COMPLETE                     ")
    print("==================================================================")
    print(f"Total Records Processed: {total_records}")
    print(f"Total Players Audited: {len(player_stats)}")
    print(f"Total Active Shops Audited: {len(shops)}")
    print(f"Total WorldGuard Regions Audited: {len(regions)}")
    print(f"Total Anomalies Identified: {len(all_anomalies)}")
    print("==================================================================")

if __name__ == "__main__":
    main()
