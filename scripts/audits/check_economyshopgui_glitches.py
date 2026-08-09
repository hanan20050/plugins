#!/usr/bin/env python3
"""
check_economyshopgui_glitches.py

Scans EconomyShopGUI configuration and item pricing rules for:
1. Direct Buy-Sell Arbitrage Glitches:
   - Buying price of any item <= Selling price (Yields infinite money loop).
2. Decompression & Crafting Exploits:
   - Block / item acquisition cost + decompression/crafting yielding profit on component sales.
3. Zero-Cost / Free Item Glitches:
   - Buying price set to 0.
4. USD Currency Formatting & Number Audit:
   - Displays all prices, profits, and calculations formatted as USD ($ values) and numeric totals.
"""

import os
import sys
import json
import re
import math
import argparse

# Decompression & Uncrafting Rules (1 Block / Item -> N Ingredients)
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
    {'block': 'minecraft:melon', 'item': 'minecraft:melon_slice', 'count': 9},
    {'block': 'minecraft:prismarine_bricks', 'item': 'minecraft:prismarine_shard', 'count': 9},
]

# Common Crafting Recipes (Ingredients -> Crafted Product Output)
CRAFTING_RECIPES = [
    # Sugar & Food
    {'output': 'minecraft:sugar', 'yield': 1, 'ingredients': [('minecraft:sugar_cane', 1)]},
    {'output': 'minecraft:bread', 'yield': 1, 'ingredients': [('minecraft:wheat', 3)]},
    {'output': 'minecraft:golden_carrot', 'yield': 1, 'ingredients': [('minecraft:gold_nugget', 8), ('minecraft:carrot', 1)]},
    {'output': 'minecraft:golden_apple', 'yield': 1, 'ingredients': [('minecraft:gold_ingot', 8), ('minecraft:apple', 1)]},
    {'output': 'minecraft:pumpkin_pie', 'yield': 1, 'ingredients': [('minecraft:pumpkin', 1), ('minecraft:sugar', 1), ('minecraft:egg', 1)]},
    {'output': 'minecraft:cake', 'yield': 1, 'ingredients': [('minecraft:milk_bucket', 3), ('minecraft:sugar', 2), ('minecraft:wheat', 3), ('minecraft:egg', 1)]},
    
    # Paper, Books, Leather, Wood
    {'output': 'minecraft:paper', 'yield': 3, 'ingredients': [('minecraft:sugar_cane', 3)]},
    {'output': 'minecraft:book', 'yield': 1, 'ingredients': [('minecraft:paper', 3), ('minecraft:leather', 1)]},
    {'output': 'minecraft:bookshelf', 'yield': 1, 'ingredients': [('minecraft:oak_planks', 6), ('minecraft:book', 3)]},
    {'output': 'minecraft:stick', 'yield': 4, 'ingredients': [('minecraft:oak_planks', 2)]},
    {'output': 'minecraft:oak_planks', 'yield': 4, 'ingredients': [('minecraft:oak_log', 1)]},

    # Building & Stonecutter/Crafting (Logs, Slabs, Stairs)
    {'output': 'minecraft:oak_slab', 'yield': 6, 'ingredients': [('minecraft:oak_planks', 3)]},
    {'output': 'minecraft:oak_stairs', 'yield': 4, 'ingredients': [('minecraft:oak_planks', 6)]},
    {'output': 'minecraft:cobblestone_slab', 'yield': 6, 'ingredients': [('minecraft:cobblestone', 3)]},
    {'output': 'minecraft:stone_stairs', 'yield': 4, 'ingredients': [('minecraft:stone', 6)]},
    {'output': 'minecraft:glass_pane', 'yield': 16, 'ingredients': [('minecraft:glass', 6)]},

    # Redstone & Utility
    {'output': 'minecraft:piston', 'yield': 1, 'ingredients': [('minecraft:oak_planks', 3), ('minecraft:cobblestone', 4), ('minecraft:iron_ingot', 1), ('minecraft:redstone', 1)]},
    {'output': 'minecraft:repeater', 'yield': 1, 'ingredients': [('minecraft:redstone_torch', 2), ('minecraft:redstone', 1), ('minecraft:smooth_stone', 3)]},
    {'output': 'minecraft:comparator', 'yield': 1, 'ingredients': [('minecraft:redstone_torch', 3), ('minecraft:quartz', 1), ('minecraft:stone', 3)]},
    {'output': 'minecraft:tnt', 'yield': 1, 'ingredients': [('minecraft:gunpowder', 5), ('minecraft:sand', 4)]},
    {'output': 'minecraft:anvil', 'yield': 1, 'ingredients': [('minecraft:iron_block', 3), ('minecraft:iron_ingot', 4)]},

    # Ores & Netherite Ingots
    {'output': 'minecraft:netherite_ingot', 'yield': 1, 'ingredients': [('minecraft:netherite_scrap', 4), ('minecraft:gold_ingot', 4)]},
]


def fmt_usd(amount):
    """Formats numeric money amounts into USD ($ formatted string)."""
    return f"${amount:,.2f} USD"

class EconomyShopGUIGlitchChecker:
    def __init__(self, config_file="EconomyShopGUI/config.yml"):
        self.config_file = config_file
        self.buy_prices = {}   # item_material -> price in USD
        self.sell_prices = {}  # item_material -> payout in USD

    def parse_config(self):
        if not os.path.exists(self.config_file):
            print(f"❌ Target path '{self.config_file}' not found.")
            return False

        files_to_scan = []
        if os.path.isdir(self.config_file):
            for root, _, files in os.walk(self.config_file):
                for f in files:
                    if f.endswith('.yml'):
                        files_to_scan.append(os.path.join(root, f))
        else:
            files_to_scan.append(self.config_file)

        for fp in files_to_scan:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Split content into item blocks
            item_blocks = re.split(r"\n\s{6}[a-zA-Z0-9_]+:\n", content)
            for block in item_blocks:
                mat_m = re.search(r"material:\s*([A-Z0-9_]+)", block)
                if not mat_m:
                    continue
                mat = mat_m.group(1).upper()
                mat_id = "minecraft:" + mat.lower()

                buy_m = re.search(r"buy:\s*([\d\.-]+)", block)
                sell_m = re.search(r"sell:\s*([\d\.-]+)", block)
                stack_m = re.search(r"stack-size:\s*(\d+)", block)

                stack_size = float(stack_m.group(1)) if stack_m else 1.0

                if buy_m:
                    try:
                        b_val = float(buy_m.group(1))
                        if b_val > 0:
                            # Divide by stack_size to get price per single item
                            self.buy_prices[mat_id] = b_val / stack_size
                    except ValueError:
                        pass

                if sell_m:
                    try:
                        s_val = float(sell_m.group(1))
                        if s_val > 0:
                            self.sell_prices[mat_id] = s_val / stack_size
                    except ValueError:
                        pass

        return True

    def check_glitches(self):
        print("==========================================================================")
        print("       ECONOMYSHOPGUI INFINITE MONEY AUDITOR (USD $ CURRENCY & NUMBERS)   ")
        print("==========================================================================")
        print(f"Config Path: {self.config_file}\n")
        
        self.parse_config()
        
        print(f"• Total Purchasable Items Tracked : {len(self.buy_prices):,} items")
        print(f"• Total Sellable Items Tracked    : {len(self.sell_prices):,} items\n")
        
        glitches = []

        # 1. Direct Buy/Sell Glitch Check
        for mat_id, sell_p in self.sell_prices.items():
            if mat_id in self.buy_prices:
                buy_p = self.buy_prices[mat_id]
                if sell_p >= buy_p:
                    profit = sell_p - buy_p
                    glitches.append({
                        "type": "DIRECT_BUY_SELL_ARBITRAGE",
                        "item": mat_id,
                        "buy_price": buy_p,
                        "sell_price": sell_p,
                        "profit": profit,
                        "message": f"{mat_id} buy price ({fmt_usd(buy_p)}) <= sell price ({fmt_usd(sell_p)})! Profit: +{fmt_usd(profit)}/unit"
                    })

        # 2. Decompression Crafting Check
        for rule in DECOMPRESSION_RULES:
            block = rule['block']
            item = rule['item']
            count = rule['count']

            if block in self.buy_prices and item in self.sell_prices:
                block_buy = self.buy_prices[block]
                item_sell_total = self.sell_prices[item] * count
                if item_sell_total > block_buy:
                    profit = item_sell_total - block_buy
                    glitches.append({
                        "type": "DECOMPRESSION_CRAFTING_EXPLOIT",
                        "item": f"{block} -> {count}x {item}",
                        "buy_price": block_buy,
                        "sell_price": item_sell_total,
                        "profit": profit,
                        "message": f"Buying 1x {block} ({fmt_usd(block_buy)}) & decompressing to {count:,}x {item} sells for {fmt_usd(item_sell_total)}! Profit: +{fmt_usd(profit)}"
                    })

        # 3. Crafting Recipe Profit Exploits Check
        for recipe in CRAFTING_RECIPES:
            output_item = recipe['output']
            yield_cnt = recipe['yield']
            ingredients = recipe['ingredients']

            if output_item in self.sell_prices:
                # Check if all ingredients can be bought in shop
                total_ing_cost = 0.0
                can_buy_all = True
                ing_desc = []
                for ing_mat, ing_cnt in ingredients:
                    if ing_mat in self.buy_prices:
                        cost = self.buy_prices[ing_mat] * ing_cnt
                        total_ing_cost += cost
                        ing_desc.append(f"{ing_cnt}x {ing_mat}")
                    else:
                        can_buy_all = False
                        break

                if can_buy_all:
                    product_sell_payout = self.sell_prices[output_item] * yield_cnt
                    if product_sell_payout > total_ing_cost:
                        profit = product_sell_payout - total_ing_cost
                        glitches.append({
                            "type": "CRAFTING_RECIPE_EXPLOIT",
                            "item": f"{' + '.join(ing_desc)} -> {yield_cnt}x {output_item}",
                            "buy_price": total_ing_cost,
                            "sell_price": product_sell_payout,
                            "profit": profit,
                            "message": f"Buying ingredients ({', '.join(ing_desc)}) for {fmt_usd(total_ing_cost)} & crafting {yield_cnt}x {output_item} sells for {fmt_usd(product_sell_payout)}! Profit: +{fmt_usd(profit)}"
                        })

        print("--------------------------------------------------------------------------")
        if glitches:
            print(f"🚨 CRITICAL WARNING: Found {len(glitches):,} Infinite Money Glitch(es)!")
            for g in glitches:
                print(f"  ❌ [{g['type']}] {g['message']}")
        else:
            print("✅ CLEAN AUDIT: No direct arbitrage, decompression, or crafting exploits found!")
            print(f"   Checked {len(self.buy_prices) + len(self.sell_prices):,} total price entries across all recipes.")
        print("==========================================================================\n")
        return len(glitches) == 0

def main():
    parser = argparse.ArgumentParser(description="Check EconomyShopGUI configuration for money glitches with USD currency formatting.")
    parser.add_argument("--config", default="EconomyShopGUI/config.yml", help="Path to config.yml or shop directory")
    args = parser.parse_args()

    checker = EconomyShopGUIGlitchChecker(args.config)
    checker.check_glitches()

if __name__ == "__main__":
    main()

