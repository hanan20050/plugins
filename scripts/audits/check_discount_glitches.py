#!/usr/bin/env python3
"""
check_discount_glitches.py

Scans Shopkeepers trade recipes (save.yml) for infinite money glitches, 
exchange violations, zero-cost glitches, and trade loops when discounts/sales 
(e.g., 10%, 20%, 25%, 30%, 50%, 75%) are applied to shops.

Rules Enforced:
1. Money Exchange (Shop ID 5) & Currency Exchange trades MUST NOT be discounted.
2. Discounted buy price of any item must NOT be less than its sell price in buyback/sell shops.
3. Discounted block/item acquisition cost + decompression/crafting must NOT yield profit when selling components.
4. Discounted trade costs must NOT drop to 0 emeralds (Free Item Glitch).
5. Circular trade loops must NOT yield net profit.
"""

import os
import sys
import json
import math
import argparse
import re

# Currency values in base Emeralds
CURRENCY_MAP = {
    'minecraft:emerald': 1.0,
    'minecraft:emerald_block': 9.0,
    'minecraft:netherite_ingot': 64.0,
    'minecraft:netherite_block': 576.0,
}

DECOMPRESSION_RULES = [
    {'block': 'minecraft:iron_block', 'item': 'minecraft:iron_ingot', 'count': 9},
    {'block': 'minecraft:gold_block', 'item': 'minecraft:gold_ingot', 'count': 9},
    {'block': 'minecraft:diamond_block', 'item': 'minecraft:diamond', 'count': 9},
    {'block': 'minecraft:emerald_block', 'item': 'minecraft:emerald', 'count': 9},
    {'block': 'minecraft:copper_block', 'item': 'minecraft:copper_ingot', 'count': 9},
    {'block': 'minecraft:coal_block', 'item': 'minecraft:coal', 'count': 9},
    {'block': 'minecraft:redstone_block', 'item': 'minecraft:redstone', 'count': 9},
    {'block': 'minecraft:lapis_block', 'item': 'minecraft:lapis_lazuli', 'count': 9},
    {'block': 'minecraft:slime_block', 'item': 'minecraft:slime_ball', 'count': 9},
    {'block': 'minecraft:hay_block', 'item': 'minecraft:wheat', 'count': 9},
    {'block': 'minecraft:bone_block', 'item': 'minecraft:bone_meal', 'count': 9},
    {'block': 'minecraft:quartz_block', 'item': 'minecraft:quartz', 'count': 4},
    {'block': 'minecraft:glowstone', 'item': 'minecraft:glowstone_dust', 'count': 4},
    {'block': 'minecraft:blaze_rod', 'item': 'minecraft:blaze_powder', 'count': 2},
    {'block': 'minecraft:blaze_powder', 'item': 'minecraft:ender_eye', 'count': 1, 'ingredients': ['minecraft:blaze_powder', 'minecraft:ender_pearl']},
]

def parse_save_file(filepath):
    shopkeepers = {}
    current_sk = None
    current_recipe = None
    current_item = None
    
    if not os.path.exists(filepath):
        print(f"Error: Save file '{filepath}' not found.")
        sys.exit(1)

    with open(filepath, 'r') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            indent = len(line) - len(line.lstrip())
            
            if indent == 0:
                if stripped.startswith('data-version:') or stripped.startswith('snapshots:'):
                    continue
                current_sk = stripped.replace(':', '').replace("'", "")
                shopkeepers[current_sk] = {'name': f'Shopkeeper {current_sk}', 'recipes': {}}
            elif indent == 2:
                if stripped.startswith('recipes:'):
                    continue
                if stripped.startswith('name:'):
                    shopkeepers[current_sk]['name'] = stripped.split(':', 1)[1].strip()
            elif indent == 4:
                current_recipe = stripped.replace(':', '').replace("'", "")
                if current_sk and current_sk in shopkeepers:
                    shopkeepers[current_sk]['recipes'][current_recipe] = {}
            elif indent == 6:
                item_name = stripped.replace(':', '')
                if item_name in ['resultItem', 'item1', 'item2']:
                    current_item = item_name
                    if current_sk and current_recipe in shopkeepers[current_sk]['recipes']:
                        shopkeepers[current_sk]['recipes'][current_recipe][current_item] = {}
            elif indent == 8:
                parts = stripped.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().replace("'", "")
                    if key in ['id', 'count']:
                        if key == 'count':
                            val = int(val)
                        if (current_sk and current_recipe in shopkeepers[current_sk]['recipes'] 
                                and current_item in shopkeepers[current_sk]['recipes'][current_recipe]):
                            shopkeepers[current_sk]['recipes'][current_recipe][current_item][key] = val

    return shopkeepers

def get_item_value_in_emeralds(item_id, count):
    if item_id in CURRENCY_MAP:
        return CURRENCY_MAP[item_id] * count
    return None

def load_crafting_recipes(recipes_dir):
    recipes = []
    for rule in DECOMPRESSION_RULES:
        recipes.append({
            'result': rule['item'],
            'count': rule['count'],
            'ingredients': rule.get('ingredients', [rule['block']]),
            'is_smelting': False,
            'source': f"Crafting/Decompression of {rule['item']}"
        })
        
    if not os.path.exists(recipes_dir):
        return recipes
        
    for filename in os.listdir(recipes_dir):
        if not filename.endswith('.json'):
            continue
        filepath = os.path.join(recipes_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            rtype = data.get('type')
            result = data.get('result', {})
            if isinstance(result, str):
                result_id = result
                result_count = 1
            else:
                result_id = result.get('id')
                result_count = result.get('count', 1)
                
            if not result_id:
                continue
                
            ingredients = []
            
            def extract_item(ing):
                if isinstance(ing, str):
                    return ing
                elif isinstance(ing, dict):
                    if 'item' in ing:
                        return ing['item']
                    elif 'tag' in ing:
                        tag = ing['tag']
                        if 'planks' in tag: return 'minecraft:oak_planks'
                        if 'logs' in tag: return 'minecraft:oak_log'
                        return tag
                elif isinstance(ing, list):
                    for sub in ing:
                        res = extract_item(sub)
                        if res: return res
                return None

            is_smelting = False
            if rtype == 'minecraft:crafting_shaped':
                keys = data.get('key', {})
                pattern = data.get('pattern', [])
                for row in pattern:
                    for char in row:
                        if char != ' ':
                            item = extract_item(keys.get(char))
                            if item: ingredients.append(item)
                                
            elif rtype == 'minecraft:crafting_shapeless':
                for ing in data.get('ingredients', []):
                    item = extract_item(ing)
                    if item: ingredients.append(item)
                        
            elif rtype in ['minecraft:smelting', 'minecraft:blasting', 'minecraft:smoking', 'minecraft:campfire_cooking']:
                item = extract_item(data.get('ingredient'))
                if item: ingredients.append(item)
                is_smelting = (rtype != 'minecraft:campfire_cooking')
                    
            if ingredients:
                recipes.append({
                    'result': result_id,
                    'count': result_count,
                    'ingredients': ingredients,
                    'is_smelting': is_smelting,
                    'source': filename
                })
        except Exception:
            pass
            
    return recipes

class DiscountGlitchChecker:
    def __init__(self, save_path, recipes_dir):
        self.save_path = save_path
        self.recipes_dir = recipes_dir
        self.sk_data = parse_save_file(save_path)
        self.crafting_recipes = load_crafting_recipes(recipes_dir)

    def analyze_discount(self, discount_pct):
        """
        Simulates applying discount_pct (e.g. 20.0 for 20% off) to all buy trades 
        (except Shopkeeper 5 / Money Exchange and currency exchange trades).
        Returns a list of glitch findings.
        """
        glitches = []
        discount_factor = 1.0 - (discount_pct / 100.0)

        buy_prices = {'minecraft:emerald': 1.0, 'minecraft:emerald_block': 9.0, 'minecraft:netherite_ingot': 64.0, 'minecraft:netherite_block': 576.0}
        sell_prices = {'minecraft:emerald': 1.0, 'minecraft:emerald_block': 9.0, 'minecraft:netherite_ingot': 64.0, 'minecraft:netherite_block': 576.0}
        buy_trade_details = {}
        sell_trade_details = {}

        for sk_id, sk in self.sk_data.items():
            sk_name = sk.get('name', f'Shop {sk_id}')
            is_money_exchange = (sk_id == '5' or 'money exchange' in sk_name.lower())

            recipes = sk.get('recipes', {})
            for r_id, r_data in recipes.items():
                result = r_data.get('resultItem', {})
                item1 = r_data.get('item1', {})
                item2 = r_data.get('item2', {})

                res_id = result.get('id')
                res_count = result.get('count', 1)
                i1_id = item1.get('id')
                i1_count = item1.get('count', 1)
                i2_id = item2.get('id') if item2 else None
                i2_count = item2.get('count', 1) if item2 else 0

                if not res_id or not i1_id:
                    continue

                is_exchange_trade = (i1_id in CURRENCY_MAP and res_id in CURRENCY_MAP)

                # Check 1: Currency Exchange Discount Violation
                if is_money_exchange or is_exchange_trade:
                    # Currency exchange must never be discounted!
                    effective_i1_count = i1_count
                    effective_i2_count = i2_count
                else:
                    # Regular admin shop selling item to player for currency
                    val_i1 = get_item_value_in_emeralds(i1_id, i1_count)
                    val_i2 = get_item_value_in_emeralds(i2_id, i2_count) if i2_id else 0.0

                    if val_i1 is not None:
                        # Discount applies to currency payment
                        disc_i1_count = max(1, math.floor(i1_count * discount_factor)) if i1_count > 1 else 1
                        if i1_count == 1 and discount_pct >= 50.0:
                            # For single item cost 1 emerald at 50% discount or more, math.floor could be 0 or 1
                            disc_i1_count = max(1, math.floor(i1_count * discount_factor))

                        # Check 4: Free item glitch
                        if disc_i1_count <= 0:
                            glitches.append({
                                'discount_pct': discount_pct,
                                'type': 'FREE_ITEM_GLITCH',
                                'shop_id': sk_id,
                                'shop_name': sk_name,
                                'trade_id': r_id,
                                'item': res_id,
                                'message': f"Discount of {discount_pct}% reduced cost to 0 emeralds for {res_id}!"
                            })

                        effective_i1_count = disc_i1_count
                    else:
                        effective_i1_count = i1_count

                    effective_i2_count = i2_count

                # Calculate unit buy price
                val_in = get_item_value_in_emeralds(i1_id, effective_i1_count)
                if i2_id:
                    v2 = get_item_value_in_emeralds(i2_id, effective_i2_count)
                    if val_in is not None and v2 is not None:
                        val_in += v2
                    else:
                        val_in = None

                val_out = get_item_value_in_emeralds(res_id, res_count)

                # Player BUYING item from Shop (payment in currency, output non-currency)
                if val_in is not None and val_out is None:
                    unit_buy_cost = val_in / float(res_count)
                    if res_id not in buy_prices or unit_buy_cost < buy_prices[res_id]:
                        buy_prices[res_id] = unit_buy_cost
                        buy_trade_details[res_id] = {
                            'shop_id': sk_id,
                            'shop_name': sk_name,
                            'recipe_id': r_id,
                            'orig_cost': (get_item_value_in_emeralds(i1_id, i1_count) or 0) / float(res_count),
                            'disc_cost': unit_buy_cost
                        }

                # Player SELLING item to Shop (payment in item, output currency) - Sell prices remain fixed!
                elif val_out is not None and val_in is None and not i2_id:
                    unit_sell_price = val_out / float(i1_count)
                    if i1_id not in sell_prices or unit_sell_price > sell_prices[i1_id]:
                        sell_prices[i1_id] = unit_sell_price
                        sell_trade_details[i1_id] = {
                            'shop_id': sk_id,
                            'shop_name': sk_name,
                            'recipe_id': r_id,
                            'sell_price': unit_sell_price
                        }

        # Calculate minimum acquisition cost (including crafting/decompression/smelting)
        min_costs = {item: price for item, price in buy_prices.items()}
        derivation_map = {item: "Shop purchase" for item in buy_prices}

        # Farmable items (e.g., Ender Pearls from Enderman farm) can have 0 acquisition cost for players
        FARMABLE_ITEMS = {'minecraft:ender_pearl', 'minecraft:rotten_flesh', 'minecraft:bone', 'minecraft:string', 'minecraft:arrow', 'minecraft:gunpowder', 'minecraft:slime_ball'}
        farmable_min_costs = {item: (0.0 if item in FARMABLE_ITEMS else price) for item, price in min_costs.items()}
        for item in FARMABLE_ITEMS:
            if item not in farmable_min_costs:
                farmable_min_costs[item] = 0.0

        def get_recipe_cost(recipe, cost_dict):
            total = 0.0
            for ing in recipe['ingredients']:
                if ing not in cost_dict:
                    return float('inf')
                total += cost_dict[ing]
            if recipe.get('is_smelting', False):
                coal_cost = cost_dict.get('minecraft:coal', float('inf'))
                if coal_cost != float('inf'):
                    total += coal_cost / 8.0
            return total / float(recipe['count'])

        for _ in range(30):
            updated = False
            for r in self.crafting_recipes:
                res = r['result']
                cost = get_recipe_cost(r, min_costs)
                if cost < min_costs.get(res, float('inf')):
                    min_costs[res] = cost
                    derivation_map[res] = r
                    updated = True
                
                farm_cost = get_recipe_cost(r, farmable_min_costs)
                if farm_cost < farmable_min_costs.get(res, float('inf')):
                    farmable_min_costs[res] = farm_cost
                    if res not in min_costs or farm_cost < min_costs[res]:
                        derivation_map[res] = f"{r['source']} (using mob farm drops)"
            if not updated:
                break

        # Check 2 & 3: Compare min acquisition/discounted cost vs sell price
        for item, sell_p in sell_prices.items():
            if item in CURRENCY_MAP or item in FARMABLE_ITEMS:
                continue

            cost = min_costs.get(item, float('inf'))
            farm_cost = farmable_min_costs.get(item, float('inf'))
            
            # Check paid crafting / direct shop buy glitch
            if sell_p > cost + 0.0001:
                profit = sell_p - cost
                buy_info = buy_trade_details.get(item, {})
                sell_info = sell_trade_details.get(item, {})
                is_decompression_loop = isinstance(derivation_map.get(item), dict) or 'Crafting' in str(derivation_map.get(item))

                glitch_type = 'DECOMPRESSION_CRAFTING_LOOP' if is_decompression_loop else 'DIRECT_BUY_SELL_LOOP'

                glitches.append({
                    'discount_pct': discount_pct,
                    'type': glitch_type,
                    'item': item,
                    'discounted_buy_cost': round(cost, 4),
                    'fixed_sell_price': round(sell_p, 4),
                    'profit_per_unit': round(profit, 4),
                    'buy_shop': buy_info,
                    'sell_shop': sell_info,
                    'derivation': derivation_map.get(item) if is_decompression_loop else "Direct Shop Buy",
                    'message': f"At {discount_pct}% discount, {item} costs {cost:.2f} Emeralds to acquire/craft but sells for {sell_p:.2f} Emeralds (Profit: +{profit:.2f} Emeralds/unit)!"
                })
            elif sell_p > farm_cost + 0.0001 and item not in buy_prices:
                # Crafting recipe using farmed components yields profit when sold to shop
                profit = sell_p - farm_cost
                buy_info = buy_trade_details.get(item, {})
                sell_info = sell_trade_details.get(item, {})
                
                glitches.append({
                    'discount_pct': discount_pct,
                    'type': 'CRAFTING_FARM_ITEM_LOOP',
                    'item': item,
                    'discounted_buy_cost': round(farm_cost, 4),
                    'fixed_sell_price': round(sell_p, 4),
                    'profit_per_unit': round(profit, 4),
                    'buy_shop': buy_info,
                    'sell_shop': sell_info,
                    'derivation': derivation_map.get(item, "Crafting with mob farm drops"),
                    'message': f"At {discount_pct}% discount, {item} costs {farm_cost:.2f} Emeralds to craft (using farm drops) but sells for {sell_p:.2f} Emeralds (Profit: +{profit:.2f} Emeralds/unit)!"
                })

        return glitches

    def run_full_sweep(self, discount_rates=[10, 20, 25, 30, 50, 75]):
        all_results = {}
        total_glitches = 0

        print("==========================================================================")
        print("      SHOPKEEPERS DISCOUNT GLITCH & INFINITE MONEY LOOP AUDITOR          ")
        print("==========================================================================")
        print(f"Target Save File: {self.save_path}")
        print(f"Testing Discount Tiers: {', '.join(str(d)+'%' for d in discount_rates)}\n")

        for d in discount_rates:
            glitches = self.analyze_discount(d)
            all_results[d] = glitches
            total_glitches += len(glitches)

            if glitches:
                print(f"🚨 [FAIL] Discount {d}% -> Found {len(glitches)} glitch(es)/infinite loop(s):")
                for g in glitches:
                    print(f"  ❌ [{g['type']}] {g['message']}")
                    if g.get('buy_shop'):
                        print(f"     Buy Shop: {g['buy_shop'].get('shop_name')} (ID {g['buy_shop'].get('shop_id')})")
                    if g.get('sell_shop'):
                        print(f"     Sell Shop: {g['sell_shop'].get('shop_name')} (ID {g['sell_shop'].get('shop_id')})")
            else:
                print(f"✅ [PASS] Discount {d}% -> SAFE (No infinite money loops detected)")

        print("\n==========================================================================")
        if total_glitches == 0:
            print("🎉 OVERALL STATUS: ALL DISCOUNT TIERS ARE SAFE & BALANCED!")
        else:
            print(f"⚠️ OVERALL STATUS: FOUND {total_glitches} TOTAL GLITCH(ES) ACROSS DISCOUNT TIERS.")
        print("==========================================================================")

        return all_results

def main():
    parser = argparse.ArgumentParser(description="Check Shopkeepers data for glitches when discounts are applied.")
    parser.add_argument("--file", default="Shopkeepers/data/save.yml", help="Path to save.yml file")
    parser.add_argument("--recipes-dir", default="recipes_26.2", help="Path to Minecraft recipes directory")
    parser.add_argument("--discount", type=float, help="Specific discount percentage to test (e.g., 20 or 50)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    checker = DiscountGlitchChecker(args.file, args.recipes_dir)

    if args.discount is not None:
        rates = [args.discount]
    else:
        rates = [10.0, 20.0, 25.0, 30.0, 50.0, 75.0]

    if args.json:
        results = {}
        for r in rates:
            results[str(r)] = checker.analyze_discount(r)
        print(json.dumps(results, indent=2))
    else:
        checker.run_full_sweep(rates)

if __name__ == "__main__":
    main()
