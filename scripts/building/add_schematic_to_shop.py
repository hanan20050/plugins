import os
import sys
import gzip
import struct
import json
import subprocess
import urllib.request
import urllib.error

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
save_path = os.path.join(PROJECT_ROOT, "Shopkeepers/data/save.yml")
sync_script = os.path.join(PROJECT_ROOT, "sync.py")

# NBT Parsing Helpers
def parse_nbt(data, pos=0):
    if pos >= len(data):
        return None, None, None, pos
    tag_type = data[pos]
    pos += 1
    if tag_type == 0:
        return 0, None, None, pos
    name_len = struct.unpack(">H", data[pos:pos+2])[0]
    pos += 2
    name = data[pos:pos+name_len].decode('utf-8', errors='ignore')
    pos += name_len
    val, pos = parse_tag_payload(tag_type, data, pos)
    return tag_type, name, val, pos

def parse_tag_payload(tag_type, data, pos):
    if tag_type == 1:
        return data[pos], pos + 1
    elif tag_type == 2:
        return struct.unpack(">h", data[pos:pos+2])[0], pos + 2
    elif tag_type == 3:
        return struct.unpack(">i", data[pos:pos+4])[0], pos + 4
    elif tag_type == 4:
        return struct.unpack(">q", data[pos:pos+8])[0], pos + 8
    elif tag_type == 5:
        return struct.unpack(">f", data[pos:pos+4])[0], pos + 4
    elif tag_type == 6:
        return struct.unpack(">d", data[pos:pos+8])[0], pos + 8
    elif tag_type == 7:
        length = struct.unpack(">i", data[pos:pos+4])[0]
        return data[pos+4:pos+4+length], pos + 4 + length
    elif tag_type == 8:
        length = struct.unpack(">H", data[pos:pos+2])[0]
        return data[pos+2:pos+2+length].decode('utf-8', errors='ignore'), pos + 2 + length
    elif tag_type == 9:
        sub_type = data[pos]
        length = struct.unpack(">i", data[pos+1:pos+5])[0]
        pos += 5
        val = []
        for _ in range(length):
            v, pos = parse_tag_payload(sub_type, data, pos)
            val.append(v)
        return val, pos
    elif tag_type == 10:
        val = {}
        while True:
            t_type = data[pos]
            if t_type == 0:
                pos += 1
                break
            res = parse_nbt(data, pos)
            if res[0] is None:
                break
            t_type, name, sub_val, pos = res
            val[name] = sub_val
        return val, pos
    elif tag_type == 11:
        length = struct.unpack(">i", data[pos:pos+4])[0]
        pos += 4
        val = []
        for _ in range(length):
            val.append(struct.unpack(">i", data[pos:pos+4])[0])
            pos += 4
        return val, pos
    elif tag_type == 12:
        length = struct.unpack(">i", data[pos:pos+4])[0]
        pos += 4
        val = []
        for _ in range(length):
            val.append(struct.unpack(">q", data[pos:pos+8])[0])
            pos += 8
        return val, pos
    return None, pos

def extract_materials(schem_path):
    if not os.path.exists(schem_path):
        print(f"Error: Schematic file '{schem_path}' not found.")
        sys.exit(1)
        
    try:
        with gzip.open(schem_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        print(f"Error reading gzip schematic: {e}")
        sys.exit(1)
        
    if data[0] != 10:
        print("Error: Invalid NBT root compound tag.")
        sys.exit(1)
        
    _, _, root, _ = parse_nbt(data)
    
    # Sponge Schematic nested structure
    schem = root
    if 'Schematic' in root:
        schem = root['Schematic']
        
    palette = {}
    if 'Palette' in schem:
        palette = schem['Palette']
    elif 'Blocks' in schem and isinstance(schem['Blocks'], dict) and 'Palette' in schem['Blocks']:
        palette = schem['Blocks']['Palette']
        
    if not palette:
        print("Warning: No block palette found in schematic.")
        return set()
        
    raw_mats = set()
    for key in palette.keys():
        mat = key.split('[')[0].strip()
        if mat not in ("minecraft:air", "minecraft:water", "minecraft:cave_air", "minecraft:void_air"):
            raw_mats.add(mat)
            
    return raw_mats

# Block state to item ID mapping
def map_block_to_item(mat):
    # Wall variants
    if mat.endswith("_wall_banner"):
        return mat.replace("_wall_banner", "_banner")
    if mat.endswith("_wall_sign"):
        return mat.replace("_wall_sign", "_sign")
    if mat.endswith("_wall_fan"):
        return mat.replace("_wall_fan", "")
    if mat.endswith("_fan"):
        return mat.replace("_fan", "")
        
    # Potted plants
    if mat.startswith("minecraft:potted_"):
        plant = mat.replace("minecraft:potted_", "minecraft:")
        # Special potted plant mappings
        if plant == "minecraft:cherry_sapling":
            return plant
        return plant
        
    # Block states without direct item names
    mappings = {
        "minecraft:tripwire": "minecraft:string",
        "minecraft:flower_pot": "minecraft:flower_pot",
        "minecraft:carrots": "minecraft:carrot",
        "minecraft:potatoes": "minecraft:potato",
        "minecraft:wheat": "minecraft:wheat",
    }
    return mappings.get(mat, mat)

def get_existing_shopkeeper_items():
    import yaml
    if not os.path.exists(save_path):
        return set()
    with open(save_path, 'r') as f:
        data = yaml.safe_load(f)
    existing = set()
    for sk_id, sk in data.items():
        if sk_id in ('data-version', 'version'):
            continue
        for r in sk.get('recipes', {}).values():
            for k in ('resultItem', 'item1', 'item2'):
                itm = r.get(k)
                if itm and 'id' in itm:
                    existing.add(itm['id'])
    return existing

# Rarity pricing heuristic
def get_heuristic_price(item_id):
    name = item_id.replace("minecraft:", "")
    # Functional / Utilities
    if name in ("bookshelf"):
        return {"count": 4, "price": 6} # Anti-exploit
    if name in ("barrel", "chest", "composter", "furnace"):
        return {"count": 8, "price": 4}
    # Rare blocks / Lights
    if any(k in name for k in ("lantern", "glowstone", "quartz", "bed", "froglight", "rod", "pot")):
        return {"count": 4, "price": 12}
    # Concrete, Terracotta, Wools, Carpets
    if any(k in name for k in ("concrete", "terracotta", "wool", "carpet", "glass", "banner", "door")):
        return {"count": 16, "price": 3}
    # Leaves / Natural
    if "leaves" in name:
        return {"count": 16, "price": 3}
    # Common building blocks
    if any(k in name for k in ("stairs", "fence", "slab", "trapdoor", "stone", "cobblestone", "planks", "block", "dirt", "grass")):
        return {"count": 16, "price": 2}
    # Default fallback
    return {"count": 8, "price": 3}

# Query Gemini API if key is present
def get_gemini_prices(items):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
        
    print("Querying Gemini API for pricing suggestions...")
    prompt = (
        "Classify the following Minecraft item IDs into rarity categories and assign shop prices in Emeralds. "
        "Each price must be a bit expensive. Return a raw JSON array of objects with keys 'item_id', 'count', and 'price'. "
        "Follow these strict rules:\n"
        "1. Bookshelf must be sold at 4 bookshelves for 6 emeralds to prevent exploits.\n"
        "2. Do not include markdown formatting or quotes outside of raw JSON text.\n\n"
        f"Items:\n{json.dumps(list(items))}"
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    req_data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    req = urllib.request.Request(
        url,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        data=json.dumps(req_data).encode("utf-8")
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            resp_data = json.loads(res.read().decode("utf-8"))
            text = resp_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Clean up potential markdown code fences
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            if text.startswith("json"):
                text = text.split("json", 1)[1].strip()
            return json.loads(text)
    except Exception as e:
        print(f"Warning: Gemini API request failed: {e}. Falling back to local pricing rules.")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 add_schematic_to_shop.py <path_to_schematic>")
        sys.exit(1)
        
    schem_path = sys.argv[1]
    
    # 1. Parse schematic
    print(f"Analyzing schematic file: {schem_path}...")
    raw_mats = extract_materials(schem_path)
    
    # 2. Map blocks to valid items
    mapped_items = set()
    for mat in raw_mats:
        mapped_items.add(map_block_to_item(mat))
        
    # 3. Filter existing items
    existing_items = get_existing_shopkeeper_items()
    missing_items = mapped_items - existing_items
    
    if not missing_items:
        print("All blocks in the schematic are already present in the shopkeepers database.")
        sys.exit(0)
        
    print(f"Found {len(missing_items)} missing items to add.")
    
    # 4. Generate prices
    trades = []
    gemini_pricing = get_gemini_prices(missing_items)
    if gemini_pricing:
        for t in gemini_pricing:
            # Simple validation
            if "item_id" in t and "count" in t and "price" in t:
                # Anti-exploit check for bookshelf
                if t["item_id"] == "minecraft:bookshelf":
                    t["count"] = 4
                    t["price"] = 6
                trades.append(t)
    
    # Fallback/Heuristic Pricing
    if not trades:
        for item in missing_items:
            price_info = get_heuristic_price(item)
            trades.append({
                "item_id": item,
                "count": price_info["count"],
                "price": price_info["price"]
            })
            
    # 5. Glitch check / validation
    # If uncrafting exploits are detected, automatically double prices
    for t in trades:
        if t["item_id"] == "minecraft:coal_block" and (t["price"] / t["count"]) < 0.6:
            # Coal blocks must cost more than 0.6 emeralds per block
            t["count"] = 8
            t["price"] = 6
            
    # 6. Surgical save
    print("Reading save.yml...")
    with open(save_path, 'r') as f:
        lines = f.readlines()
        
    insert_idx = -1
    for idx, line in enumerate(lines):
        if 'snapshots:' in line:
            insert_idx = idx
            break
            
    if insert_idx == -1:
        print("Error: Could not locate 'snapshots:' section for Shopkeeper 1.")
        sys.exit(1)
        
    # Scan backward for last recipe ID
    last_recipe_id = 93
    for idx in range(insert_idx - 1, 0, -1):
        line = lines[idx].strip()
        if line.endswith("':") and line.startswith("'"):
            try:
                last_recipe_id = int(line.replace("'", "").replace(":", ""))
                break
            except ValueError:
                pass
                
    next_id = last_recipe_id + 1
    print(f"Adding new trades starting from recipe ID: {next_id}")
    
    new_yaml_lines = []
    for t in trades:
        new_yaml_lines.extend([
            f"    '{next_id}':\n",
            "      resultItem:\n",
            "        DataVersion: 4903\n",
            f"        id: {t['item_id']}\n",
            f"        count: {t['count']}\n",
            "      item1:\n",
            "        DataVersion: 4903\n",
            "        id: minecraft:emerald\n",
            f"        count: {t['price']}\n"
        ])
        next_id += 1
        
    # Insert new lines
    lines = lines[:insert_idx] + new_yaml_lines + lines[insert_idx:]
    
    with open(save_path, 'w') as f:
        f.writelines(lines)
        
    print(f"Surgically added {len(trades)} trades to Shopkeeper 1 locally.")
    
    # 7. Push to server and reload
    print("Pushing Shopkeepers/data/save.yml to server...")
    subprocess.run(["python3", sync_script, "push", "Shopkeepers/data/save.yml"])
    
    # 8. Send player broadcast
    print("Broadcasting updates to players in-game...")
    # Group items by category to display nicely
    catalog_msg = [
        "",
        {"text": "\n========================================\n", "color": "gold"},
        {"text": "✨ SHOP CATALOG UPDATED (New Schematic Blocks) ✨\n", "color": "yellow", "bold": True},
        {"text": f"Added {len(trades)} new items to General Store:\n\n", "color": "green"}
    ]
    # List top 10 items as preview
    for t in trades[:12]:
        name_clean = t['item_id'].replace("minecraft:", "").replace("_", " ").title()
        catalog_msg.append({"text": f" • {name_clean}: {t['count']} for {t['price']} Emeralds\n", "color": "white"})
    if len(trades) > 12:
        catalog_msg.append({"text": f" ...and {len(trades) - 12} more items!\n", "color": "gray"})
        
    catalog_msg.extend([
        {"text": "\n🛒 Visit General Store & Build Shop (Shopkeeper 1) to buy!\n", "color": "aqua", "bold": True},
        {"text": "========================================\n", "color": "gold"}
    ])
    
    # Send tellraw command via Exaroton API console
    TOKEN = os.environ.get("EXAROTON_TOKEN") or "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
    SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or "cEuS61sZvNEFS3aB"
    tellraw_cmd = f"tellraw @a {json.dumps(catalog_msg)}"
    
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/command"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        data=json.dumps({"command": tellraw_cmd}).encode("utf-8")
    )
    try:
        urllib.request.urlopen(req)
        print("✔ Broadcast sent successfully!")
    except Exception as e:
        print(f"Warning: Failed to send tellraw command: {e}")

if __name__ == '__main__':
    main()
