import re

CURRENCY_RATES = {
    'minecraft:emerald': 1.0,
    'minecraft:emerald_block': 9.0,
    'minecraft:netherite_ingot': 64.0,
    'minecraft:netherite_block': 576.0
}

def analyze_save_yml():
    with open("Shopkeepers/data/save.yml", "r") as f:
        content = f.read()

    # Split shopkeeper entries by 'N': at line start
    raw_shops = re.split(r"\n(?='[0-9]+':)", content)

    buy_prices = {}   # item_id -> list of {unit_price, shop_id, shop_name}
    sell_prices = {}  # item_id -> list of {unit_payout, shop_id, shop_name}

    for shop_block in raw_shops:
        shop_id_m = re.search(r"^'([0-9]+)':", shop_block.strip())
        if not shop_id_m:
            continue
        shop_id = shop_id_m.group(1)

        name_m = re.search(r"^\s+name:\s*'(.*)'", shop_block, re.MULTILINE)
        shop_name = name_m.group(1) if name_m else f"Shop {shop_id}"

        # Split recipes by 'N': inside recipes block
        recipe_blocks = re.split(r"\n\s+'[0-9]+':", shop_block)
        
        for r_block in recipe_blocks[1:]:
            # Parse resultItem
            res_id_m = re.search(r"resultItem:\s*\n(?:\s+.*\n)*?\s+id:\s*(minecraft:[a_z0-9_]+)", r_block)
            res_cnt_m = re.search(r"resultItem:\s*\n(?:\s+.*\n)*?\s+count:\s*([0-9]+)", r_block)

            if not res_id_m:
                continue

            res_id = res_id_m.group(1)
            res_cnt = float(res_cnt_m.group(1)) if res_cnt_m else 1.0

            # Parse item1 and item2
            items = []
            for item_key in ['item1', 'item2']:
                item_m = re.search(item_key + r":\s*\n(?:\s+.*\n)*?\s+id:\s*(minecraft:[a_z0-9_]+)", r_block)
                cnt_m = re.search(item_key + r":\s*\n(?:\s+.*\n)*?\s+count:\s*([0-9]+)", r_block)
                if item_m:
                    items.append({
                        'id': item_m.group(1),
                        'count': float(cnt_m.group(1)) if cnt_m else 1.0
                    })

            if not items:
                continue

            # Check if all inputs are pure currency
            total_cost_emerald = 0.0
            all_currency_inputs = True
            for inp in items:
                inp_id = inp['id']
                inp_cnt = inp['count']
                if inp_id in CURRENCY_RATES:
                    total_cost_emerald += CURRENCY_RATES[inp_id] * inp_cnt
                else:
                    all_currency_inputs = False

            # BUYING: Player pays emeralds -> receives item
            if all_currency_inputs and res_id not in CURRENCY_RATES:
                unit_buy_cost = total_cost_emerald / res_cnt
                if res_id not in buy_prices:
                    buy_prices[res_id] = []
                buy_prices[res_id].append({
                    'unit_price': unit_buy_cost,
                    'shop_id': shop_id,
                    'shop_name': shop_name
                })

            # SELLING: Player hands item -> receives emeralds
            if res_id in CURRENCY_RATES and len(items) == 1:
                inp_id = items[0]['id']
                inp_cnt = items[0]['count']
                if inp_id not in CURRENCY_RATES:
                    total_payout_emerald = CURRENCY_RATES[res_id] * res_cnt
                    unit_payout = total_payout_emerald / inp_cnt
                    if inp_id not in sell_prices:
                        sell_prices[inp_id] = []
                    sell_prices[inp_id].append({
                        'unit_payout': unit_payout,
                        'shop_id': shop_id,
                        'shop_name': shop_name
                    })

    print("==================================================")
    print("      SHOPKEEPER MONEY LOOP & GLITCH AUDIT        ")
    print("==================================================")
    print(f"Total Unique Items Purchasable: {len(buy_prices)}")
    print(f"Total Unique Items Sellable   : {len(sell_prices)}")

    glitches = []
    for item_id, s_list in sell_prices.items():
        max_sell = max(s_list, key=lambda x: x['unit_payout'])
        
        if item_id in buy_prices:
            min_buy = min(buy_prices[item_id], key=lambda x: x['unit_price'])
            
            # Glitch exists if sell price per unit > buy price per unit!
            if max_sell['unit_payout'] > min_buy['unit_price']:
                profit = max_sell['unit_payout'] - min_buy['unit_price']
                glitches.append({
                    'item': item_id,
                    'buy_price': min_buy['unit_price'],
                    'buy_shop': f"Shop {min_buy['shop_id']} ({min_buy['shop_name']})",
                    'sell_payout': max_sell['unit_payout'],
                    'sell_shop': f"Shop {max_sell['shop_id']} ({max_sell['shop_name']})",
                    'profit': profit
                })

    print("\n--------------------------------------------------")
    if glitches:
        print(f"🚨 CRITICAL WARNING: Found {len(glitches)} Infinite Money Glitch(es)!")
        for g in glitches:
            print(f"\n[GLITCH DETECTED] Item: {g['item']}")
            print(f"  • Buy Price  : {g['buy_price']:.4f} Emeralds/unit from {g['buy_shop']}")
            print(f"  • Sell Payout: {g['sell_payout']:.4f} Emeralds/unit at {g['sell_shop']}")
            print(f"  • Profit     : +{g['profit']:.4f} Emeralds per item traded!")
    else:
        print("✅ CLEAN AUDIT: No infinite money loops or arbitrage price glitches found!")
    print("--------------------------------------------------")

if __name__ == "__main__":
    analyze_save_yml()
