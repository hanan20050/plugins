#!/usr/bin/env python3
import os
import sys
import json
import yaml
import glob

# Setup paths relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

save_path = os.path.join(PROJECT_ROOT, "Shopkeepers/data/save.yml")
prices_master_path = os.path.join(PROJECT_ROOT, "shop_prices_master.yml")
recipes_dir = os.path.join(PROJECT_ROOT, "recipes_26.2")

CURRENCY_VALUES = {
    'minecraft:emerald': 1.0,
    'minecraft:emerald_block': 9.0,
    'minecraft:netherite_ingot': 64.0,
    'minecraft:netherite_block': 576.0
}

def get_item_info(item_dict):
    if not item_dict:
        return None
    return item_dict.get('id'), item_dict.get('count', 1)

def get_currency_value(item_id, count):
    if item_id in CURRENCY_VALUES:
        return CURRENCY_VALUES[item_id] * count
    return None

def extract_item_ids(ing_val):
    if not ing_val:
        return []
    if isinstance(ing_val, str):
        return [ing_val]
    if isinstance(ing_val, dict):
        if 'item' in ing_val:
            return [ing_val['item']]
        if 'tag' in ing_val:
            return [ing_val['tag']]
    if isinstance(ing_val, list):
        res = []
        for x in ing_val:
            res.extend(extract_item_ids(x))
        return res
    return []

def main():
    print("==================================================")
    print("      ECONOMY SHOP & CRAFTING GLITCH AUDIT       ")
    print("==================================================")
    
    # 1. Parse Shopkeepers
    sk_buy_prices = {}
    sk_sell_prices = {}
    duplicates = []
    currency_violations = []
    
    if os.path.exists(save_path):
        with open(save_path, 'r') as f:
            sk_data = yaml.safe_load(f)
            
        # Helper for strict duplicates check
        def get_item_signature(item_dict):
            if not item_dict:
                return None
            item_id = item_dict.get('id')
            count = item_dict.get('count', 1)
            components = item_dict.get('components', {})
            components_str = json.dumps(components, sort_keys=True)
            return (item_id, count, components_str)

        for sk_id, sk_val in sk_data.items():
            if sk_id in ('data-version', 'version'):
                continue
            name = sk_val.get('name', f"Shopkeeper {sk_id}")
            recipes = sk_val.get('recipes', {})
            if not recipes:
                continue
                
            seen_trades = set()
            for recipe_id, recipe in recipes.items():
                r_item = recipe.get('resultItem')
                i1_item = recipe.get('item1')
                i2_item = recipe.get('item2')
                
                r_id, r_count = get_item_info(r_item) or (None, 0)
                i1_id, i1_count = get_item_info(i1_item) or (None, 0)
                i2_id, i2_count = get_item_info(i2_item) or (None, 0)
                
                # Check duplicates
                r_sig = get_item_signature(r_item)
                i1_sig = get_item_signature(i1_item)
                i2_sig = get_item_signature(i2_item)
                trade_sig = (r_sig, i1_sig, i2_sig)
                if trade_sig in seen_trades:
                    duplicates.append((sk_id, name, recipe_id))
                else:
                    seen_trades.add(trade_sig)
                
                # Check exchange trades rule: only allowed in shopkeeper 5
                is_exchange = (r_id in CURRENCY_VALUES) and (i1_id in CURRENCY_VALUES) and (i2_id is None or i2_id in CURRENCY_VALUES)
                if is_exchange and str(sk_id) != '5':
                    currency_violations.append((sk_id, name, recipe_id, f"{i1_count} {i1_id} -> {r_count} {r_id}"))

                # Buying prices (Emerald Economy)
                if r_id and r_id not in CURRENCY_VALUES:
                    val1 = get_currency_value(i1_id, i1_count)
                    val2 = get_currency_value(i2_id, i2_count) if i2_id else 0.0
                    if val1 is not None and (i2_id is None or val2 is not None):
                        cost_per_unit = (val1 + val2) / r_count
                        if r_id not in sk_buy_prices or cost_per_unit < sk_buy_prices[r_id]:
                            sk_buy_prices[r_id] = cost_per_unit
                            
                # Selling prices (Emerald Economy)
                elif r_id in CURRENCY_VALUES:
                    if i1_id and i1_id not in CURRENCY_VALUES and not i2_id:
                        payout_per_unit = get_currency_value(r_id, r_count) / i1_count
                        if i1_id not in sk_sell_prices or payout_per_unit > sk_sell_prices[i1_id]:
                            sk_sell_prices[i1_id] = payout_per_unit
    else:
        print(f"⚠️  Shopkeepers save file not found at: {save_path}")

    # 2. Parse EconomyShopGUI Prices
    esg_buy_prices = {}
    esg_sell_prices = {}
    if os.path.exists(prices_master_path):
        with open(prices_master_path, 'r') as f:
            esg_data = yaml.safe_load(f)
        categories = esg_data.get('categories', {})
        for cat_id, cat_val in categories.items():
            items = cat_val.get('items', [])
            for item in items:
                mat = item.get('material', '').lower()
                if not mat:
                    continue
                full_id = f"minecraft:{mat}"
                buy = item.get('buy', 0.0)
                sell = item.get('sell', 0.0)
                if buy > 0.0:
                    esg_buy_prices[full_id] = buy
                if sell > 0.0:
                    esg_sell_prices[full_id] = sell
    else:
        print(f"⚠️  EconomyShopGUI master prices not found at: {prices_master_path}")

    # Print duplicates & violations
    print("\n--- [1] Structural Shopkeeper Checks ---")
    if duplicates:
        print(f"❌ Found {len(duplicates)} TRUE duplicate trades (same items & components):")
        for d in duplicates:
            print(f"  - Shop {d[0]} ({d[1]}) | Recipe {d[2]}")
    else:
        print("✔ No duplicate trades found.")

    if currency_violations:
        print(f"❌ Found {len(currency_violations)} currency exchange violations (outside shop 5):")
        for v in currency_violations:
            print(f"  - Shop {v[0]} ({v[1]}) | Recipe {v[2]}: {v[3]}")
    else:
        print("✔ Currency exchange rule verified (restricted to shop 5).")

    # Direct Glitches Check
    print("\n--- [2] Direct Buy/Sell Price Checks ---")
    direct_sk_glitches = []
    for item_id, sell_p in sk_sell_prices.items():
        if item_id in sk_buy_prices and sell_p > sk_buy_prices[item_id]:
            direct_sk_glitches.append((item_id, sk_buy_prices[item_id], sell_p))
            
    if direct_sk_glitches:
        print("❌ Direct Shopkeeper Glitches Found (Sell Price > Buy Price):")
        for g in direct_sk_glitches:
            print(f"  - {g[0]} | Buy: {g[1]:.2f} Emeralds | Sell: {g[2]:.2f} Emeralds")
    else:
        print("✔ No direct Shopkeeper price glitches.")

    direct_esg_glitches = []
    for item_id, sell_p in esg_sell_prices.items():
        if item_id in esg_buy_prices and sell_p > esg_buy_prices[item_id]:
            direct_esg_glitches.append((item_id, esg_buy_prices[item_id], sell_p))
            
    if direct_esg_glitches:
        print("❌ Direct EconomyShopGUI Glitches Found (Sell Price > Buy Price):")
        for g in direct_esg_glitches:
            print(f"  - {g[0]} | Buy: {g[1]:.2f} $ | Sell: {g[2]:.2f} $")
    else:
        print("✔ No direct EconomyShopGUI price glitches.")

    # 3. Crafting Glitches Check
    print("\n--- [3] Crafting Recipe Glitches Check ---")
    recipe_files = glob.glob(os.path.join(recipes_dir, "*.json"))
    if not recipe_files:
        print(f"⚠️  No recipe JSON files found at: {recipes_dir}")
        return

    recipes = []
    for filepath in recipe_files:
        try:
            with open(filepath, 'r') as f:
                r_json = json.load(f)
        except Exception:
            continue
            
        recipe_type = r_json.get('type')
        result = r_json.get('result', {})
        res_id = result.get('id')
        res_count = result.get('count', 1)
        
        if not res_id:
            continue
            
        ingredients = {}
        if recipe_type == "minecraft:crafting_shaped":
            pattern = r_json.get('pattern', [])
            key_map = r_json.get('key', {})
            resolved_keys = {char: extract_item_ids(ing) for char, ing in key_map.items()}
            for row in pattern:
                for char in row:
                    if char == ' ':
                        continue
                    possible_items = resolved_keys.get(char, [])
                    if possible_items:
                        item = possible_items[0]
                        ingredients[item] = ingredients.get(item, 0) + 1
                        
        elif recipe_type == "minecraft:crafting_shapeless":
            ing_list = r_json.get('ingredients', [])
            for ing in ing_list:
                possible_items = extract_item_ids(ing)
                if possible_items:
                    item = possible_items[0]
                    ingredients[item] = ingredients.get(item, 0) + 1
                    
        elif recipe_type in ("minecraft:smelting", "minecraft:blasting", "minecraft:smoking", "minecraft:campfire_cooking", "minecraft:stonecutting"):
            ing = r_json.get('ingredient')
            possible_items = extract_item_ids(ing)
            if possible_items:
                item = possible_items[0]
                ingredients[item] = 1
                
        recipes.append({
            'file': os.path.basename(filepath),
            'result': res_id,
            'count': res_count,
            'ingredients': ingredients
        })

    def run_crafting_eval(buy_prices, sell_prices, label_currency):
        glitches_found = []
        for r in recipes:
            res_id = r['result']
            res_cnt = r['count']
            ing_dict = r['ingredients']
            if not ing_dict:
                continue
                
            all_buyable = True
            total_buy_cost = 0.0
            breakdown = []
            
            for ing_id, ing_cnt in ing_dict.items():
                tag_mappings = {
                    'minecraft:planks': 'minecraft:oak_planks',
                    'minecraft:logs': 'minecraft:oak_log',
                    'minecraft:coals': 'minecraft:coal'
                }
                mapped_id = tag_mappings.get(ing_id, ing_id)
                if mapped_id in buy_prices:
                    cost = buy_prices[mapped_id] * ing_cnt
                    total_buy_cost += cost
                    breakdown.append(f"{ing_cnt}x {mapped_id.replace('minecraft:', '')} ({buy_prices[mapped_id]:.2f} each)")
                else:
                    all_buyable = False
                    break
                    
            if all_buyable and res_id in sell_prices:
                sell_payout = sell_prices[res_id] * res_cnt
                if sell_payout > total_buy_cost:
                    profit = sell_payout - total_buy_cost
                    glitches_found.append({
                        'recipe': r['file'],
                        'result': f"{res_cnt}x {res_id.replace('minecraft:', '')}",
                        'cost': total_buy_cost,
                        'payout': sell_payout,
                        'profit': profit,
                        'breakdown': ", ".join(breakdown)
                    })
        
        print(f"\n* Crafting Glitches in {label_currency} Economy:")
        if glitches_found:
            for g in glitches_found:
                print(f"  [GLITCH] Craft '{g['result']}' via '{g['recipe']}'")
                print(f"    Ingredients Cost: {g['cost']:.3f} ({g['breakdown']})")
                print(f"    Selling Payout  : {g['payout']:.3f}")
                print(f"    PROFIT          : +{g['profit']:.3f} per craft!")
        else:
            print("  ✔ No crafting glitches found.")

    run_crafting_eval(sk_buy_prices, sk_sell_prices, "Shopkeepers (Emerald)")
    run_crafting_eval(esg_buy_prices, esg_sell_prices, "EconomyShopGUI (Vault $)")
    print("==================================================")

if __name__ == "__main__":
    main()
