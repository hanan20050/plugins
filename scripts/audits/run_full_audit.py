#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import re
from datetime import datetime

# Load Player Identity Reference
PLAYER_MAPPING = {
    ".mustafahacker67": "mustafa",
    ".HastyBag7675": "muhammad saleh",
    ".WiryCircle3938": "omer saleh",
    "hanansaleh": "hanan saleh",
    "manan2007": "manan saleh",
    "manan200502007": "manan saleh",
    ".manan2007": "manan saleh",
    "NightmareDady": "rayan saleh",
    ".AzanSaleh": "azan saleh",
    "azansalehhh": "azan saleh"
}

# Unstackable item types (max stack 1)
UNSTACKABLE_KEYWORDS = [
    "_sword", "_pickaxe", "_axe", "_shovel", "_hoe",
    "_helmet", "_chestplate", "_leggings", "_boots",
    "bow", "crossbow", "trident", "shield", "elytra",
    "shears", "flint_and_steel", "fishing_rod",
    "saddle", "horse_armor", "written_book", "enchanted_book",
    "totem_of_undying", "shulker_box"
]

# 16-stackable items
SIXTEEN_STACKABLE = [
    "ender_pearl", "egg", "snowball", "bucket",
    "honey_bottle", "sign", "banner"
]

def is_unstackable(item_id):
    item = item_id.lower().replace("minecraft:", "")
    for kw in UNSTACKABLE_KEYWORDS:
        if kw in item:
            return True
    return False

def is_16_stackable(item_id):
    item = item_id.lower().replace("minecraft:", "")
    for kw in SIXTEEN_STACKABLE:
        if kw in item:
            return True
    return False

def get_max_stack(item_id):
    if is_unstackable(item_id):
        return 1
    if is_16_stackable(item_id):
        return 16
    return 64

def get_emerald_value(item_id, count):
    item = item_id.lower().replace("minecraft:", "")
    if item == "emerald":
        return count
    elif item == "emerald_block":
        return count * 9
    elif item == "netherite_ingot":
        return count * 64
    elif item == "netherite_block":
        return count * 576
    return 0

def parse_save_yml(filepath="Shopkeepers/data/save.yml"):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r") as f:
        content = f.read()

    # Split shopkeepers by top-level key e.g. '1':
    shops_raw = re.split(r'\n(\'?\d+\'?):\n', content)
    shops = {}
    
    for i in range(1, len(shops_raw), 2):
        shop_id = shops_raw[i].strip("'")
        shop_body = shops_raw[i+1]
        
        name_m = re.search(r'name:\s*[\'\"]?(.*?)[\'\"]?\n', shop_body)
        shop_name = name_m.group(1) if name_m else f"Shop #{shop_id}"
        
        type_m = re.search(r'type:\s*[\'\"]?(.*?)[\'\"]?\n', shop_body)
        shop_type = type_m.group(1) if type_m else "admin"

        x_m = re.search(r'x:\s*(-?\d+)', shop_body)
        y_m = re.search(r'y:\s*(-?\d+)', shop_body)
        z_m = re.search(r'z:\s*(-?\d+)', shop_body)
        world_m = re.search(r'world:\s*(\w+)', shop_body)

        x = int(x_m.group(1)) if x_m else 0
        y = int(y_m.group(1)) if y_m else 0
        z = int(z_m.group(1)) if z_m else 0
        world = world_m.group(1) if world_m else "world"

        recipes_raw = re.split(r'\n\s{4}(\'\d+\'|\d+):\n', shop_body)
        recipes = []
        
        for r_idx in range(1, len(recipes_raw), 2):
            rec_id = recipes_raw[r_idx].strip("'")
            rec_body = recipes_raw[r_idx+1]
            
            res_m = re.search(r'resultItem:.*?\n\s+DataVersion:.*?\n\s+id:\s*(minecraft:\w+)\n\s+count:\s*(\d+)', rec_body, re.DOTALL)
            i1_m = re.search(r'item1:.*?\n\s+DataVersion:.*?\n\s+id:\s*(minecraft:\w+)\n\s+count:\s*(\d+)', rec_body, re.DOTALL)
            i2_m = re.search(r'item2:.*?\n\s+DataVersion:.*?\n\s+id:\s*(minecraft:\w+)\n\s+count:\s*(\d+)', rec_body, re.DOTALL)
            
            res_id = res_m.group(1) if res_m else ""
            res_cnt = int(res_m.group(2)) if res_m else 0
            
            i1_id = i1_m.group(1) if i1_m else ""
            i1_cnt = int(i1_m.group(2)) if i1_m else 0

            i2_id = i2_m.group(1) if i2_m else ""
            i2_cnt = int(i2_m.group(2)) if i2_m else 0
            
            recipes.append({
                "recipe_id": rec_id,
                "item1_id": i1_id,
                "item1_count": i1_cnt,
                "item2_id": i2_id,
                "item2_count": i2_cnt,
                "result_id": res_id,
                "result_count": res_cnt
            })
            
        shops[shop_id] = {
            "id": shop_id,
            "name": shop_name,
            "type": shop_type,
            "world": world,
            "x": x, "y": y, "z": z,
            "recipes": recipes
        }
    return shops

print("Parser initialized successfully!")
