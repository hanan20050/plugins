#!/usr/bin/env python3
import os
import sqlite3
import json
import re
from datetime import datetime

PLAYER_TARGETS = {
    "rayan saleh": ["NightmareDady", "rayan saleh"],
    "azan saleh": ["azansalehhh", ".AzanSaleh", "AzanSaleh", "azan saleh"],
    "manan saleh": ["manansaleh2007", "manan2007", "manan200502007", ".manan2007", "manan saleh"]
}

KNOWN_UUIDS = {
    "rayan saleh": "d413c28e-64bb-32af-9661-3e901bc6e22b",
    "azan saleh": "2d5bf9b3-5a85-3026-a136-4680097f11f1",
    "manan saleh": "95204d3f-ea6c-3dfa-929d-9180927184f8"
}

CURRENCY_RATES = {
    "minecraft:emerald": 1,
    "EMERALD": 1,
    "minecraft:emerald_block": 9,
    "EMERALD_BLOCK": 9,
    "minecraft:netherite_ingot": 64,
    "NETHERITE_INGOT": 64,
    "minecraft:netherite_block": 576,
    "NETHERITE_BLOCK": 576
}

def analyze_player_trades(db_paths):
    records = {
        "rayan saleh": [],
        "azan saleh": [],
        "manan saleh": []
    }

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
            p_name = row[col_idx["player_name"]]
            target_matched = None

            if p_name in PLAYER_TARGETS["rayan saleh"] or "nightmaredady" in p_name.lower():
                target_matched = "rayan saleh"
            elif p_name in PLAYER_TARGETS["azan saleh"] or "azansaleh" in p_name.lower():
                target_matched = "azan saleh"
            elif p_name in PLAYER_TARGETS["manan saleh"] or "manan" in p_name.lower():
                target_matched = "manan saleh"

            if target_matched:
                ts = row[col_idx["timestamp"]]
                s_x = row[col_idx["shop_x"]]
                s_y = row[col_idx["shop_y"]]
                s_z = row[col_idx["shop_z"]]
                s_type = row[col_idx["shop_type"]]
                s_owner = row[col_idx.get("shop_owner_name")] or "Admin"

                i1_type = row[col_idx["item_1_type"]] or ""
                i1_amt = row[col_idx["item_1_amount"]] or 0
                i2_type = row[col_idx.get("item_2_type")] or ""
                i2_amt = row[col_idx.get("item_2_amount")] or 0
                res_type = row[col_idx["result_item_type"]] or ""
                res_amt = row[col_idx["result_item_amount"]] or 0
                t_count = row[col_idx["trade_count"]] or 1

                records[target_matched].append({
                    "timestamp": ts,
                    "shop_coords": (s_x, s_y, s_z),
                    "shop_type": s_type,
                    "shop_owner": s_owner,
                    "item1": (i1_type, i1_amt * t_count),
                    "item2": (i2_type, i2_amt * t_count),
                    "result": (res_type, res_amt * t_count),
                    "count": t_count
                })

    return records

def parse_regions_for_players():
    player_regions = {
        "rayan saleh": [],
        "azan saleh": [],
        "manan saleh": []
    }
    base_dir = "WorldGuard/worlds"
    if not os.path.exists(base_dir):
        return player_regions

    for world in os.listdir(base_dir):
        r_file = os.path.join(base_dir, world, "regions.yml")
        if not os.path.exists(r_file):
            continue
        with open(r_file, "r") as f:
            content = f.read()

        regions_raw = re.split(r'\n\s{4}(\w+):\n', content)
        for i in range(1, len(regions_raw), 2):
            r_name = regions_raw[i]
            r_body = regions_raw[i+1]

            min_m = re.search(r'min:\s*\{x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)\}', r_body)
            max_m = re.search(r'max:\s*\{x:\s*(-?\d+),\s*y:\s*(-?\d+),\s*z:\s*(-?\d+)\}', r_body)

            min_x = int(min_m.group(1)) if min_m else 0
            min_y = int(min_m.group(2)) if min_m else 0
            min_z = int(min_m.group(3)) if min_m else 0
            max_x = int(max_m.group(1)) if max_m else 0
            max_y = int(max_m.group(2)) if max_m else 0
            max_z = int(max_m.group(3)) if max_m else 0

            width = (max_x - min_x) + 1
            length = (max_z - min_z) + 1

            for p_key, p_uuid in KNOWN_UUIDS.items():
                if p_uuid in r_body or p_key in r_body.lower() or any(alias.lower() in r_body.lower() for alias in PLAYER_TARGETS[p_key]):
                    player_regions[p_key].append({
                        "world": world,
                        "region": r_name,
                        "bounds": f"({min_x}, {min_y}, {min_z}) to ({max_x}, {max_y}, {max_z})",
                        "size": f"{width}x{length}",
                        "body": r_body
                    })
    return player_regions

def generate_report():
    db_paths = ["Shopkeepers/trade-logs/trades.db", "backup_trades_db_hanan_delete.db"]
    records = analyze_player_trades(db_paths)
    regions = parse_regions_for_players()

    artifact_dir = "/Users/hanansaleh/.gemini/antigravity-ide/brain/61452776-0c51-498e-bf1b-cc281fa7c163"
    artifact_path = os.path.join(artifact_dir, "rayan_azan_manan_audit_report.md")

    lines = []
    lines.append("# Detailed Audit Report: Rayan Saleh, Azan Saleh & Manan Saleh")
    lines.append(f"**Generated:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n")

    for p_key in ["rayan saleh", "azan saleh", "manan saleh"]:
        p_recs = records[p_key]
        p_regs = regions[p_key]

        lines.append(f"## 👤 Player Profile: {p_key.upper()}")
        lines.append(f"- **Primary Account UUID:** `{KNOWN_UUIDS[p_key]}`")
        lines.append(f"- **Aliases / In-Game Names:** `{', '.join(PLAYER_TARGETS[p_key])}`")
        lines.append(f"- **Total Recorded Trade Transactions:** `{len(p_recs)}`")

        if p_recs:
            lines.append(f"- **First Active Timestamp:** `{p_recs[0]['timestamp']}`")
            lines.append(f"- **Last Active Timestamp:** `{p_recs[-1]['timestamp']}`")

        items_given = {}
        items_received = {}
        shops_visited = {}
        total_emerald_spent = 0
        total_emerald_gained = 0

        for r in p_recs:
            s_coord = f"{r['shop_coords'][0]},{r['shop_coords'][1]},{r['shop_coords'][2]}"
            shops_visited[s_coord] = shops_visited.get(s_coord, 0) + r["count"]

            i1_t, i1_c = r["item1"]
            i2_t, i2_c = r["item2"]
            res_t, res_c = r["result"]

            if i1_t:
                items_given[i1_t] = items_given.get(i1_t, 0) + i1_c
                total_emerald_spent += CURRENCY_RATES.get(i1_t, 0) * i1_c
            if i2_t:
                items_given[i2_t] = items_given.get(i2_t, 0) + i2_c
                total_emerald_spent += CURRENCY_RATES.get(i2_t, 0) * i2_c
            if res_t:
                items_received[res_t] = items_received.get(res_t, 0) + res_c
                total_emerald_gained += CURRENCY_RATES.get(res_t, 0) * res_c

        net_balance = total_emerald_gained - total_emerald_spent

        lines.append("\n### 💰 Currency & Value Flow")
        lines.append(f"- **Total Emerald Value Spent in Shops:** `{total_emerald_spent}` Emeralds")
        lines.append(f"- **Total Emerald Value Gained from Shops:** `{total_emerald_gained}` Emeralds")
        lines.append(f"- **Net Emerald Currency Balance:** `{net_balance}` Emeralds\n")

        lines.append("### 📦 Complete Items Provided (Given to Shops)")
        lines.append("| Item ID | Total Quantity Provided |")
        lines.append("|---|---|")
        for itype, icnt in sorted(items_given.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| `{itype}` | {icnt:,} |")

        lines.append("\n### 🎁 Complete Items Received (Obtained from Shops)")
        lines.append("| Item ID | Total Quantity Received |")
        lines.append("|---|---|")
        for itype, icnt in sorted(items_received.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| `{itype}` | {icnt:,} |")

        lines.append("\n### 🏪 Shop Locations Visited")
        lines.append("| Shop Coordinates | Trade Executions Count |")
        lines.append("|---|---|")
        for s_coord, s_cnt in sorted(shops_visited.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| `{s_coord}` | {s_cnt:,} |")

        lines.append("\n### 🏞️ WorldGuard Region Claims")
        if not p_regs:
            lines.append("*No dedicated WorldGuard region claims found under this player's name/UUID.*")
        else:
            lines.append("| World | Region Name | Dimensions | Bounds |")
            lines.append("|---|---|---|---|")
            for reg in p_regs:
                lines.append(f"| `{reg['world']}` | `{reg['region']}` | {reg['size']} | `{reg['bounds']}` |")

        lines.append("\n" + "="*50 + "\n")

    with open(artifact_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Report written to: file://{artifact_path}")

if __name__ == "__main__":
    generate_report()
