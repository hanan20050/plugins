import sys
import re

def parse_simple_yaml(filepath):
    shops = {}
    current_shop = None
    current_recipe = None
    current_section = None
    
    with open(filepath, "r") as f:
        for line in f:
            raw = line.rstrip("\n")
            stripped = raw.strip()
            indent = len(raw) - len(raw.lstrip(" "))
            
            if indent == 0 and stripped.endswith(":") and stripped.strip("':").isdigit():
                current_shop = stripped.strip("':")
                shops[current_shop] = {"name": "", "recipes": []}
                current_recipe = None
                continue
            
            if current_shop:
                if stripped.startswith("name:"):
                    name_val = stripped.split("name:", 1)[1].strip().strip("'\"")
                    shops[current_shop]["name"] = name_val
                    continue
                
                if indent == 4 and stripped.endswith(":") and stripped.strip("':").isdigit():
                    current_recipe = {"item1": {}, "item2": {}, "resultItem": {}}
                    shops[current_shop]["recipes"].append(current_recipe)
                    current_section = None
                    continue
                
                if current_recipe:
                    if stripped in ["item1:", "item2:", "resultItem:"]:
                        current_section = stripped.rstrip(":")
                        continue
                    
                    if current_section:
                        if stripped.startswith("id:"):
                            item_id = stripped.split("id:", 1)[1].strip()
                            current_recipe[current_section]["id"] = item_id
                        elif stripped.startswith("count:"):
                            count = int(stripped.split("count:", 1)[1].strip())
                            current_recipe[current_section]["count"] = count
                        elif stripped.startswith("display-name:"):
                            dname = stripped.split("display-name:", 1)[1].strip().strip("'\"")
                            current_recipe[current_section]["name"] = dname
                        elif stripped.startswith("title:"):
                            tname = stripped.split("title:", 1)[1].strip().strip("'\"")
                            current_recipe[current_section]["name"] = tname

    return shops

shops = parse_simple_yaml("Shopkeepers/data/save.yml")

CURRENCY_RATES = {
    "minecraft:emerald": 1.0,
    "minecraft:emerald_block": 9.0,
    "minecraft:netherite_ingot": 64.0,
    "minecraft:netherite_block": 576.0
}

buy_items = {}
sell_items = {}

for sid, sdata in shops.items():
    sname = sdata["name"]
    for r in sdata["recipes"]:
        i1 = r["item1"]
        i2 = r["item2"]
        res = r["resultItem"]
        
        if "id" in i1 and i1["id"] in CURRENCY_RATES and ("id" not in i2 or i2["id"] in CURRENCY_RATES):
            c1 = CURRENCY_RATES[i1["id"]] * i1.get("count", 1)
            c2 = CURRENCY_RATES[i2["id"]] * i2.get("count", 1) if "id" in i2 else 0
            total_c = c1 + c2
            if "id" in res and res["id"] not in CURRENCY_RATES:
                res_id = res["id"]
                res_cnt = res.get("count", 1)
                unit_cost = total_c / res_cnt
                buy_items.setdefault(res_id, []).append((unit_cost, res_cnt, total_c, sid, sname))
                
        if "id" in res and res["id"] in CURRENCY_RATES:
            total_payout = CURRENCY_RATES[res["id"]] * res.get("count", 1)
            if "id" in i1 and i1["id"] not in CURRENCY_RATES:
                item_id = i1["id"]
                item_cnt = i1.get("count", 1)
                unit_payout = total_payout / item_cnt
                sell_items.setdefault(item_id, []).append((unit_payout, item_cnt, total_payout, sid, sname))

print("=== MARGIN COMPARISON (BUY PRICE vs SELL PAYOUT) ===")
print(f"{'Item ID':<32} | {'Buy Cost/Unit':<15} | {'Sell Payout/Unit':<18} | {'Spread (Buy/Sell)':<18} | {'Status'}")
print("-" * 105)

all_matched_keys = set(buy_items.keys()).union(set(sell_items.keys()))

glitches = []
warnings = []
oddities = []

for item in sorted(all_matched_keys):
    buys = buy_items.get(item, [])
    sells = sell_items.get(item, [])
    
    if buys and sells:
        min_b_cost = buys[0][0]
        max_s_payout = sells[0][0]
        ratio = min_b_cost / max_s_payout if max_s_payout > 0 else 0
        status = "OK"
        if max_s_payout >= min_b_cost:
            status = "🚨 EXPLOIT"
            glitches.append((item, min_b_cost, max_s_payout))
        elif ratio > 10.0:
            status = "⚠️ VERY HIGH COST"
            warnings.append((item, min_b_cost, max_s_payout, ratio))
        elif ratio < 1.3:
            status = "⚠️ LOW SPREAD"
            warnings.append((item, min_b_cost, max_s_payout, ratio))
        print(f"{item:<32} | {min_b_cost:<15.3f} | {max_s_payout:<18.3f} | {ratio:<18.2f}x | {status}")
    elif buys:
        print(f"{item:<32} | {buys[0][0]:<15.3f} | {'N/A (Buy Only)':<18} | {'N/A':<18} | Buy-only")
    elif sells:
        print(f"{item:<32} | {'N/A (Sell Only)':<15} | {sells[0][0]:<18.3f} | {'N/A':<18} | Sell-only")
