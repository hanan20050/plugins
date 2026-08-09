#!/usr/bin/env python3
import os
import sqlite3
import json
import re
from datetime import datetime

PLAYER_MAP = {
    ".mustafahacker67": "mustafa",
    "mustafahacker67": "mustafa",
    ".MUSTAFAhacker67": "mustafa",
    ".HastyBag7675": "muhammad saleh",
    "HastyBag7675": "muhammad saleh",
    ".WiryCircle3938": "omer saleh",
    "WiryCircle3938": "omer saleh",
    "hanansaleh": "hanan saleh",
    "manan2007": "manan saleh",
    "manan200502007": "manan saleh",
    ".manan2007": "manan saleh",
    "manansaleh2007": "manan saleh",
    "NightmareDady": "rayan saleh",
    ".AzanSaleh": "azan saleh",
    "azansalehhh": "azan saleh",
    "AzanSaleh": "azan saleh"
}

KNOWN_UUIDS = {
    "rayan saleh": "d413c28e-64bb-32af-9661-3e901bc6e22b",
    "azan saleh": "2d5bf9b3-5a85-3026-a136-4680097f11f1",
    "manan saleh": "95204d3f-ea6c-3dfa-929d-9180927184f8",
    "hanan saleh": "f3a2b109-775b-432a-a912-32b04f11b223",
    "mustafa": "d54316be-00b8-3e4b-9721-36a5b6f3c11a",
    "omer saleh": "7c23c52e-0a56-32d8-bf5b-d368e5470d0b"
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

def resolve_player(raw_name):
    if not raw_name:
        return "Unknown"
    clean = str(raw_name).strip()
    if clean in PLAYER_MAP:
        return PLAYER_MAP[clean]
    for k, v in PLAYER_MAP.items():
        if clean.lower() == k.lower():
            return v
    return clean

def audit_all_item_distributions():
    db_paths = ["Shopkeepers/trade-logs/trades.db", "backup_trades_db_hanan_delete.db"]
    player_data = {}
    item_distribution = {}

    total_executions = 0

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
            total_executions += 1
            p_name = row[col_idx["player_name"]]
            real_p = resolve_player(p_name)

            i1_t = row[col_idx["item_1_type"]] or ""
            i1_a = (row[col_idx["item_1_amount"]] or 0) * (row[col_idx["trade_count"]] or 1)

            i2_t = row[col_idx.get("item_2_type")] or ""
            i2_a = (row[col_idx.get("item_2_amount")] or 0) * (row[col_idx["trade_count"]] or 1)

            res_t = row[col_idx["result_item_type"]] or ""
            res_a = (row[col_idx["result_item_amount"]] or 0) * (row[col_idx["trade_count"]] or 1)

            if real_p not in player_data:
                player_data[real_p] = {
                    "items_provided": {},
                    "items_received": {},
                    "total_trades": 0,
                    "emerald_spent": 0,
                    "emerald_gained": 0
                }

            pd = player_data[real_p]
            pd["total_trades"] += (row[col_idx["trade_count"]] or 1)

            if i1_t:
                pd["items_provided"][i1_t] = pd["items_provided"].get(i1_t, 0) + i1_a
                pd["emerald_spent"] += CURRENCY_RATES.get(i1_t, 0) * i1_a
            if i2_t:
                pd["items_provided"][i2_t] = pd["items_provided"].get(i2_t, 0) + i2_a
                pd["emerald_spent"] += CURRENCY_RATES.get(i2_t, 0) * i2_a

            if res_t:
                pd["items_received"][res_t] = pd["items_received"].get(res_t, 0) + res_a
                pd["emerald_gained"] += CURRENCY_RATES.get(res_t, 0) * res_a

                # Track global item distribution by recipient
                if res_t not in item_distribution:
                    item_distribution[res_t] = {}
                item_distribution[res_t][real_p] = item_distribution[res_t].get(real_p, 0) + res_a

    artifact_dir = "/Users/hanansaleh/.gemini/antigravity-ide/brain/61452776-0c51-498e-bf1b-cc281fa7c163"
    artifact_path = os.path.join(artifact_dir, "item_distribution_all_players.md")
    os.makedirs(artifact_dir, exist_ok=True)

    lines = []
    lines.append("# 📦 Lifetime Item Provenance & Distribution Audit (All Players)")
    lines.append(f"**Audit Execution Timestamp:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
    lines.append(f"**Total Trade Executions Analyzed:** `{total_executions}` Across All Historical Logs\n")

    lines.append("> [!IMPORTANT]")
    lines.append("> This report contains a complete side-by-side comparison of **every single item** provided to or received from shopkeepers by **Rayan Saleh**, **Azan Saleh**, **Manan Saleh**, **Hanan Saleh**, **Mustafa**, and **Omer Saleh**.\n")

    lines.append("## 🌟 1. Special Focus: Rayan Saleh vs Azan Saleh vs Server Population")
    lines.append("| Item Category / Item ID | Rayan Saleh | Azan Saleh | Manan Saleh | Hanan Saleh | Mustafa | Omer Saleh | Total Dispensed |")
    lines.append("|---|---|---|---|---|---|---|---|")

    # Get all distinct received items
    all_res_items = sorted(item_distribution.keys())
    for item_id in all_res_items:
        r_amt = item_distribution[item_id].get("rayan saleh", 0)
        a_amt = item_distribution[item_id].get("azan saleh", 0)
        m_amt = item_distribution[item_id].get("manan saleh", 0)
        h_amt = item_distribution[item_id].get("hanan saleh", 0)
        mus_amt = item_distribution[item_id].get("mustafa", 0)
        o_amt = item_distribution[item_id].get("omer saleh", 0)
        tot = sum(item_distribution[item_id].values())

        lines.append(f"| `{item_id}` | **{r_amt:,}** | **{a_amt:,}** | {m_amt:,} | {h_amt:,} | {mus_amt:,} | {o_amt:,} | **{tot:,}** |")

    lines.append("\n---\n")
    lines.append("## 📤 2. Items Provided (Given to Shops) Side-by-Side Comparison")
    
    # Collect all items provided
    all_prov_items = set()
    for pd in player_data.values():
        all_prov_items.update(pd["items_provided"].keys())

    lines.append("| Item ID Provided | Rayan Saleh | Azan Saleh | Manan Saleh | Hanan Saleh | Mustafa | Omer Saleh | Total Traded In |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for item_id in sorted(all_prov_items):
        r_amt = player_data.get("rayan saleh", {}).get("items_provided", {}).get(item_id, 0)
        a_amt = player_data.get("azan saleh", {}).get("items_provided", {}).get(item_id, 0)
        m_amt = player_data.get("manan saleh", {}).get("items_provided", {}).get(item_id, 0)
        h_amt = player_data.get("hanan saleh", {}).get("items_provided", {}).get(item_id, 0)
        mus_amt = player_data.get("mustafa", {}).get("items_provided", {}).get(item_id, 0)
        o_amt = player_data.get("omer saleh", {}).get("items_provided", {}).get(item_id, 0)
        tot = r_amt + a_amt + m_amt + h_amt + mus_amt + o_amt

        lines.append(f"| `{item_id}` | **{r_amt:,}** | **{a_amt:,}** | {m_amt:,} | {h_amt:,} | {mus_amt:,} | {o_amt:,} | **{tot:,}** |")

    lines.append("\n---\n")
    lines.append("## 🔍 3. High-Value & Rare Items Distribution Breakdown")
    lines.append("Detailed analysis of who received the server's most valuable items:\n")

    valuable_items = ["DIAMOND", "NETHERITE_INGOT", "ENCHANTED_BOOK", "ELYTRA", "TOTEM_OF_UNDYING", "SHULKER_SHELL", "VILLAGER_SPAWN_EGG", "DIAMOND_CHESTPLATE", "DIAMOND_SWORD", "ALLAY_SPAWN_EGG", "END_PORTAL_FRAME", "BARRIER"]

    for vitem in valuable_items:
        if vitem in item_distribution:
            lines.append(f"### Valuable Item: `{vitem}`")
            dist = item_distribution[vitem]
            tot_v = sum(dist.values())
            for p, cnt in sorted(dist.items(), key=lambda x: x[1], reverse=True):
                pct = (cnt / tot_v) * 100 if tot_v > 0 else 0
                lines.append(f"- **{p.upper()}**: `{cnt}` units ({pct:.1f}% of server total)")
            lines.append("")

    with open(artifact_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Deep item distribution report generated at: file://{artifact_path}")

if __name__ == "__main__":
    audit_all_item_distributions()
