import os
import re

files_and_items = {
    "EconomyShopGUI/sections/Building/wood.yml": [
        ("EMERALD", 0.0, 3.0),
        ("EMERALD_BLOCK", 0.0, 27.0),
        ("NETHERITE_INGOT", 0.0, 192.0),
        ("NETHERITE_BLOCK", 0.0, 1728.0)
    ],
    "EconomyShopGUI/sections/Building/stone.yml": [
        ("EMERALD", 0.0, 3.0),
        ("EMERALD_BLOCK", 0.0, 27.0),
        ("NETHERITE_INGOT", 0.0, 192.0),
        ("NETHERITE_BLOCK", 0.0, 1728.0)
    ],
    "EconomyShopGUI/sections/Building/natural.yml": [
        ("EMERALD", 0.0, 3.0),
        ("EMERALD_BLOCK", 0.0, 27.0),
        ("NETHERITE_INGOT", 0.0, 192.0),
        ("NETHERITE_BLOCK", 0.0, 1728.0)
    ],
    "EconomyShopGUI/sections/Building/decorative_blocks.yml": [
        ("EMERALD", 0.0, 3.0),
        ("EMERALD_BLOCK", 0.0, 27.0),
        ("NETHERITE_INGOT", 0.0, 192.0),
        ("NETHERITE_BLOCK", 0.0, 1728.0)
    ],
    "EconomyShopGUI/sections/Combat/armor.yml": [
        ("EMERALD", 0.0, 3.0),
        ("EMERALD_BLOCK", 0.0, 27.0),
        ("NETHERITE_INGOT", 0.0, 192.0),
        ("NETHERITE_BLOCK", 0.0, 1728.0)
    ],
    "EconomyShopGUI/sections/Combat/redstone.yml": [
        ("EMERALD", 0.0, 3.0),
        ("EMERALD_BLOCK", 0.0, 27.0),
        ("NETHERITE_INGOT", 0.0, 192.0),
        ("NETHERITE_BLOCK", 0.0, 1728.0)
    ]
}

for filepath, cash_in_items in files_and_items.items():
    with open(filepath, "r") as f:
        text = f.read()
        
    if "items:" in text:
        header = text.split("items:")[0].rstrip() + "\nitems:\n"
    else:
        header = text.rstrip() + "\nitems:\n"

    existing_items = []
    blocks = re.findall(r"material:\s*([A-Z0-9_]+)[\s\S]*?(?:buy:\s*([0-9.]+))?[\s\S]*?sell:\s*([0-9.]+)", text)
    
    for mat, buy, sell in blocks:
        if mat not in ["EMERALD", "EMERALD_BLOCK", "NETHERITE_INGOT", "NETHERITE_BLOCK"]:
            existing_items.append({"material": mat, "buy": float(buy) if buy else 0.0, "sell": float(sell)})

    all_items = []
    for c_mat, c_buy, c_sell in cash_in_items:
        all_items.append({"material": c_mat, "buy": c_buy, "sell": c_sell})
    all_items.extend(existing_items)

    new_yaml = header
    for idx, it in enumerate(all_items, 1):
        mat_val = it["material"]
        buy_val = it["buy"]
        sell_val = it["sell"]
        new_yaml += f"  {idx}:\n"
        new_yaml += f"    material: {mat_val}\n"
        if buy_val > 0:
            new_yaml += f"    buy: {buy_val}\n"
        new_yaml += f"    sell: {sell_val}\n"

    with open(filepath, "w") as f:
        f.write(new_yaml)

    print("Added cash-in items to:", filepath)
