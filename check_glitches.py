import os
import json
import math
import sys

def parse_save_file(filepath):
    shopkeepers = {}
    current_sk = None
    current_recipe = None
    current_item = None
    
    with open(filepath, 'r') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            indent = len(line) - len(line.lstrip())
            
            if indent == 0:
                if stripped.startswith('data-version:'):
                    continue
                current_sk = stripped.replace(':', '').replace("'", "")
                shopkeepers[current_sk] = {'recipes': {}}
            elif indent == 2:
                if stripped.startswith('recipes:'):
                    continue
                if stripped.startswith('name:'):
                    shopkeepers[current_sk]['name'] = stripped.split(':', 1)[1].strip()
            elif indent == 4:
                current_recipe = stripped.replace(':', '').replace("'", "")
                shopkeepers[current_sk]['recipes'][current_recipe] = {}
            elif indent == 6:
                item_name = stripped.replace(':', '')
                if item_name in ['resultItem', 'item1', 'item2']:
                    current_item = item_name
                    shopkeepers[current_sk]['recipes'][current_recipe][current_item] = {}
            elif indent == 8:
                parts = stripped.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().replace("'", "")
                    if key in ['id', 'count']:
                        if key == 'count':
                            val = int(val)
                        shopkeepers[current_sk]['recipes'][current_recipe][current_item][key] = val

    return shopkeepers

def value_in_emeralds(item_id, count):
    if item_id == 'minecraft:emerald':
        return count
    elif item_id == 'minecraft:netherite_ingot':
        return count * 64
    return None

# Built-in decompression / unpacking rules (e.g. 1 Block -> N Items)
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
]

def load_recipes(recipes_dir):
    recipes = []
    
    # 1. Add builtin decompression recipes
    for rule in DECOMPRESSION_RULES:
        recipes.append({
            'result': rule['item'],
            'count': rule['count'],
            'ingredients': [rule['block']],
            'is_smelting': False,
            'source': f"Decompression of {rule['block']}"
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
                        if 'planks' in tag:
                            return 'minecraft:oak_planks'
                        if 'logs' in tag:
                            return 'minecraft:oak_log'
                        return tag
                elif isinstance(ing, list):
                    for sub in ing:
                        res = extract_item(sub)
                        if res:
                            return res
                return None

            is_smelting = False
            if rtype == 'minecraft:crafting_shaped':
                keys = data.get('key', {})
                pattern = data.get('pattern', [])
                for row in pattern:
                    for char in row:
                        if char != ' ':
                            ing_val = keys.get(char)
                            item = extract_item(ing_val)
                            if item:
                                ingredients.append(item)
                                
            elif rtype == 'minecraft:crafting_shapeless':
                ings = data.get('ingredients', [])
                for ing in ings:
                    item = extract_item(ing)
                    if item:
                        ingredients.append(item)
                        
            elif rtype in ['minecraft:smelting', 'minecraft:blasting', 'minecraft:smoking', 'minecraft:campfire_cooking']:
                ing = data.get('ingredient')
                item = extract_item(ing)
                if item:
                    ingredients.append(item)
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

class AdvancedAnalyzer:
    def __init__(self):
        self.save_path = '/Users/hanansaleh/Downloads/plugins/Shopkeepers/data/save.yml'
        self.recipes_dir = '/Users/hanansaleh/Downloads/plugins/recipes_26.2'
        
        self.sk_data = parse_save_file(self.save_path)
        self.crafting_recipes = load_recipes(self.recipes_dir)
        
        self.buy_prices = {'minecraft:emerald': 1.0, 'minecraft:netherite_ingot': 64.0}
        self.sell_prices = {'minecraft:emerald': 1.0, 'minecraft:netherite_ingot': 64.0}
        self.sell_trade_map = {} # item_id -> (sk_id, recipe_id, current_sell_count)
        
        self.parse_shopkeeper_prices()
        
        self.min_costs = {}
        self.derivation_recipes = {}
        
        self.calculate_min_costs()
        
    def parse_shopkeeper_prices(self):
        for sk_id, sk in self.sk_data.items():
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
                    
                # Buying
                val_in = value_in_emeralds(i1_id, i1_count)
                if i2_id:
                    val_in2 = value_in_emeralds(i2_id, i2_count)
                    if val_in is not None and val_in2 is not None:
                        val_in += val_in2
                    else:
                        val_in = None
                        
                val_out = value_in_emeralds(res_id, res_count)
                
                if val_in is not None and val_out is None:
                    cost_per_unit = val_in / res_count
                    if res_id not in self.buy_prices or cost_per_unit < self.buy_prices[res_id]:
                        self.buy_prices[res_id] = cost_per_unit
                        
                # Selling
                elif val_out is not None and val_in is None:
                    if not i2_id:
                        sell_per_unit = val_out / i1_count
                        if i1_id not in self.sell_prices or sell_per_unit > self.sell_prices[i1_id]:
                            self.sell_prices[i1_id] = sell_per_unit
                            self.sell_trade_map[i1_id] = (sk_id, r_id, i1_count, val_out)

    def calculate_min_costs(self):
        self.min_costs = {item: price for item, price in self.buy_prices.items()}
        self.derivation_recipes = {item: "Shop purchase" for item in self.buy_prices}
        
        def get_recipe_cost(recipe):
            total = 0.0
            for ing in recipe['ingredients']:
                if ing not in self.min_costs:
                    return float('inf')
                total += self.min_costs[ing]
            
            if recipe.get('is_smelting', False):
                fuel_cost = self.min_costs.get('minecraft:coal', float('inf'))
                if fuel_cost != float('inf'):
                    total += fuel_cost / 8.0
                    
            return total / recipe['count']

        for _ in range(30):
            updated = False
            for r in self.crafting_recipes:
                res = r['result']
                cost = get_recipe_cost(r)
                if cost < self.min_costs.get(res, float('inf')):
                    self.min_costs[res] = cost
                    self.derivation_recipes[res] = r
                    updated = True
            if not updated:
                break

    def get_glitches(self):
        glitches = []
        for item, sell_price in self.sell_prices.items():
            if item in ['minecraft:emerald', 'minecraft:netherite_ingot']:
                continue
                
            cost = self.min_costs.get(item, float('inf'))
            if sell_price > cost + 0.0001:
                trade_info = self.sell_trade_map.get(item)
                glitches.append({
                    'item': item,
                    'cost': cost,
                    'sell': sell_price,
                    'trade_info': trade_info
                })
        return glitches

    def print_derivation_tree(self, item_id, count=1, indent=0):
        prefix = "  " * indent
        cost = self.min_costs.get(item_id, float('inf'))
        cost_str = f"{cost * count:.4f} Em" if cost != float('inf') else "Unknown Cost"
        
        deriv = self.derivation_recipes.get(item_id)
        if deriv == "Shop purchase" or not deriv:
            print(f"{prefix}- {count:.2f}x {item_id} ({cost_str}) [Shop Purchase]")
        else:
            print(f"{prefix}+ {count:.2f}x {item_id} ({cost_str}) [{deriv['source']}]")
            ing_counts = {}
            for ing in deriv['ingredients']:
                ing_counts[ing] = ing_counts.get(ing, 0) + 1
                
            scale = count / deriv['count']
            for ing, ing_count in ing_counts.items():
                self.print_derivation_tree(ing, ing_count * scale, indent + 1)
                
            if deriv.get('is_smelting', False):
                fuel_count = (1.0 / 8.0) * scale
                coal_cost = self.min_costs.get('minecraft:coal', 0)
                print(f"{prefix}  - {fuel_count:.3f}x minecraft:coal ({coal_cost * fuel_count:.4f} Em) [Smelting Fuel]")

    def run_exploit_report(self):
        print("==================================================")
        print("   ADVANCED MULTI-SHOP & BLOCK UNPACKING SCAN     ")
        print("==================================================")
        
        glitches = self.get_glitches()
        if glitches:
            print(f"\n🚨 WARNING: {len(glitches)} Infinite Money Glitch(es) Detected! 🚨")
            for g in glitches:
                item = g['item']
                cost = g['cost']
                sell = g['sell']
                profit = sell - cost
                print(f"\nExploit Item: {item}")
                print(f"  - Production Cost:   {cost:.4f} Emeralds")
                print(f"  - Sell Price:        {sell:.4f} Emeralds")
                print(f"  - Profit per Unit:   +{profit:.4f} Emeralds")
                print("  - Optimal Production Derivation Tree:")
                self.print_derivation_tree(item, 1, 2)
        else:
            print("\n✅ Success: No infinite money glitches detected!")
            print("All craftable & unpackable items cost more to produce than they sell for.")
        print("\n==================================================")

    def auto_patch_glitches(self):
        glitches = self.get_glitches()
        if not glitches:
            print("No glitches to patch. Everything is balanced!")
            return
            
        print(f"Found {len(glitches)} glitch(es). Calculating safe balances...")
        
        # We will read save.yml and apply safe selling counts
        with open(self.save_path, 'r') as f:
            lines = f.readlines()
            
        patches_made = 0
        for g in glitches:
            info = g['trade_info']
            if not info:
                continue
            sk_id, r_id, current_count, emerald_out = info
            cost_per_unit = g['cost']
            
            # To be non-exploitable, sell_price_per_unit must be <= cost_per_unit
            # emerald_out / required_count <= cost_per_unit
            # required_count >= emerald_out / cost_per_unit
            safe_required_count = math.ceil(emerald_out / cost_per_unit)
            # Add a small buffer to ensure margin
            if safe_required_count * cost_per_unit <= emerald_out:
                safe_required_count += 1
                
            print(f"Patching {g['item']} (Shopkeeper {sk_id}, Recipe {r_id}): count {current_count} -> {safe_required_count}")
            
            # Apply patch in line memory
            in_target_sk = False
            in_target_recipe = False
            in_item1 = False
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                indent = len(line) - len(line.lstrip())
                
                if indent == 0 and stripped.replace("'", "").replace(":", "") == str(sk_id):
                    in_target_sk = True
                elif indent == 0 and in_target_sk and stripped != f"'{sk_id}':":
                    in_target_sk = False
                    
                if in_target_sk and indent == 4 and stripped.replace("'", "").replace(":", "") == str(r_id):
                    in_target_recipe = True
                elif in_target_sk and indent == 4 and in_target_recipe and stripped != f"'{r_id}':":
                    in_target_recipe = False
                    
                if in_target_recipe and indent == 6 and stripped == "item1:":
                    in_item1 = True
                elif in_target_recipe and indent == 6 and in_item1 and stripped != "item1:":
                    in_item1 = False
                    
                if in_item1 and indent == 8 and stripped.startswith("count:"):
                    lines[i] = f"        count: {safe_required_count}\n"
                    patches_made += 1
                    break
                    
        with open(self.save_path, 'w') as f:
            f.writelines(lines)
            
        print(f"Successfully applied {patches_made} patch(es) to save.yml!")

def cli_menu():
    analyzer = AdvancedAnalyzer()
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == '--report-only':
            analyzer.run_exploit_report()
            return
        elif arg == '--auto-fix':
            analyzer.auto_patch_glitches()
            return
        elif arg == '--export-json':
            glitches = analyzer.get_glitches()
            report = {
                'status': 'FAIL' if glitches else 'PASS',
                'glitches_count': len(glitches),
                'glitches': glitches
            }
            print(json.dumps(report, indent=2))
            return

    while True:
        print("\n--- Advanced Recipe Checker Menu ---")
        print("1. Run Full Exploit Scan (With Block Unpacking & Fuel)")
        print("2. Search Item & Print Derivation Tree")
        print("3. Auto-Patch & Fix Glitches in save.yml (--auto-fix)")
        print("4. Export Audit Report as JSON")
        print("5. Exit")
        
        try:
            choice = input("Enter choice (1-5): ").strip()
            if choice == '1':
                analyzer.run_exploit_report()
            elif choice == '2':
                item_name = input("Enter item ID (e.g. 'bow' or 'minecraft:iron_ingot'): ").strip()
                if not item_name.startswith('minecraft:'):
                    item_name = 'minecraft:' + item_name
                if item_name in analyzer.min_costs:
                    print(f"\nOptimal Production Route for {item_name}:")
                    analyzer.print_derivation_tree(item_name)
                else:
                    print(f"\nItem '{item_name}' not found.")
            elif choice == '3':
                analyzer.auto_patch_glitches()
                # Re-initialize to refresh costs
                analyzer = AdvancedAnalyzer()
            elif choice == '4':
                glitches = analyzer.get_glitches()
                print(json.dumps({'status': 'FAIL' if glitches else 'PASS', 'glitches': glitches}, indent=2))
            elif choice == '5':
                break
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

if __name__ == '__main__':
    cli_menu()
