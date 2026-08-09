#!/usr/bin/env python3
"""
Automated Shopkeeper Trade & Infinite Money Glitch Audit Script
Checks save.yml for infinite buy/sell loops and audits player earnings from trades.db.
"""

import urllib.request
import json
import sqlite3
import yaml
import os

TOKEN = os.environ.get("EXAROTON_TOKEN", "")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID", "")

if not TOKEN or not SERVER_ID:
    with open(".env") as f:
        for line in f:
            if line.startswith("EXAROTON_TOKEN="): TOKEN = line.strip().split("=", 1)[1]
            if line.startswith("EXAROTON_SERVER_ID="): SERVER_ID = line.strip().split("=", 1)[1]

def api_get(endpoint):
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/{endpoint}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return resp.read()

def pull_files():
    print("[1/3] Pulling latest save.yml and trades.db from Exaroton...")
    save_yml_data = api_get("files/data/plugins/Shopkeepers/data/save.yml")
    os.makedirs("Shopkeepers/data", exist_ok=True)
    with open("Shopkeepers/data/save.yml", "wb") as f:
        f.write(save_yml_data)

    os.makedirs("Shopkeepers/trade-logs", exist_ok=True)
    try:
        trades_db_data = api_get("files/data/plugins/Shopkeepers/trade-logs/trades.db")
        with open("Shopkeepers/trade-logs/trades.db", "wb") as f:
            f.write(trades_db_data)
        print("  - Files updated successfully.")
    except Exception as e:
        print("  - Note: trades.db fetch skipped or not available:", e)

def check_glitches():
    print("\n[2/3] Checking save.yml for Infinite Money Glitches...")
    with open("Shopkeepers/data/save.yml") as f:
        data = yaml.safe_load(f)

    # Convert items to standard Heavy Core equivalent rates
    # 1 Heavy Core = 1 HC, 1 Emerald = 0.5 HC
    sk1_buy = {}  # item -> (buy_qty, hc_cost)
    sk4_sell = {} # item -> (sell_qty, hc_yield)

    def parse_item(item):
        if not item or not isinstance(item, dict): return None, 0
        return item.get("id"), item.get("count", 1)

    # Buy Shop (ID 1)
    for r_id, r in data.get("1", {}).get("recipes", {}).items():
        t1, c1 = parse_item(r.get("item1"))
        tr, cr = parse_item(r.get("resultItem"))
        if t1 == "minecraft:heavy_core" and tr and cr > 0:
            sk1_buy[tr] = (cr, float(c1))
        elif t1 == "minecraft:emerald" and tr and cr > 0:
            sk1_buy[tr] = (cr, c1 / 2.0)

    # Sell Shop (ID 4)
    for r_id, r in data.get("4", {}).get("recipes", {}).items():
        t1, c1 = parse_item(r.get("item1"))
        tr, cr = parse_item(r.get("resultItem"))
        if tr == "minecraft:heavy_core" and t1 and c1 > 0:
            sk4_sell[t1] = (c1, float(cr))
        elif tr == "minecraft:emerald" and t1 and c1 > 0:
            sk4_sell[t1] = (c1, cr / 2.0)

    glitches_found = []
    for item, (buy_qty, buy_cost) in sk1_buy.items():
        if item in sk4_sell:
            sell_qty, sell_yield = sk4_sell[item]
            cost_per_item = buy_cost / buy_qty
            yield_per_item = sell_yield / sell_qty

            if yield_per_item > cost_per_item:
                glitches_found.append({
                    "item": item,
                    "buy_qty": buy_qty,
                    "buy_cost": buy_cost,
                    "sell_qty": sell_qty,
                    "sell_yield": sell_yield,
                    "cost_per_item": cost_per_item,
                    "yield_per_item": yield_per_item
                })
                print(f"  [CRITICAL GLITCH] {item}:")
                print(f"    Buy Rate:  {buy_qty}x for {buy_cost} HC ({cost_per_item:.4f} HC/item)")
                print(f"    Sell Rate: {sell_qty}x for {sell_yield} HC ({yield_per_item:.4f} HC/item)")
                print(f"    PROFIT:    {(yield_per_item - cost_per_item):.4f} HC profit PER ITEM bought!")

    if not glitches_found:
        print("  - NO INFINITE BUY/SELL GLITCHES DETECTED!")
    return glitches_found

def audit_player_earnings():
    print("\n[3/3] Auditing Player Earnings from trades.db...")
    if not os.path.exists("Shopkeepers/trade-logs/trades.db"):
        print("  - trades.db not found locally.")
        return

    conn = sqlite3.connect("Shopkeepers/trade-logs/trades.db")
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT player_name, item_1_type, item_1_amount, result_item_type, result_item_amount, SUM(trade_count),
           SUM(CASE WHEN result_item_type = 'HEAVY_CORE' THEN result_item_amount * trade_count
                    WHEN result_item_type = 'EMERALD' THEN (result_item_amount * trade_count) / 2.0
                    ELSE 0 END) as total_hc_earned
    FROM trade 
    WHERE result_item_type IN ('HEAVY_CORE', 'EMERALD') AND shop_uuid != '5'
    GROUP BY player_name, item_1_type 
    ORDER BY player_name, total_hc_earned DESC;
    ''')

    current_player = None
    for r in cursor.fetchall():
        player, item, in_amt, out_type, out_amt, trades, hc_earned = r
        if player != current_player:
            current_player = player
            print(f"\n--- Player: {player} ---")
        print(f"  {item:25s}: Sold {in_amt}x for {out_amt} {out_type} ({trades:4d} times) -> Total Earned: {hc_earned:.1f} Heavy Cores")

if __name__ == "__main__":
    pull_files()
    check_glitches()
    audit_player_earnings()
