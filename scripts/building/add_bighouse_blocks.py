import os
import sys
import subprocess

# Paths setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
save_path = os.path.join(PROJECT_ROOT, "Shopkeepers/data/save.yml")
backup_path = save_path + ".bak"

# 46 missing blocks from BigHouse.schem (excluding air/water)
new_trades = [
    # 1. Common / Building Blocks (16 for 2 Emeralds)
    {"id": "minecraft:grass_block", "count": 16, "price": 2},
    {"id": "minecraft:acacia_stairs", "count": 16, "price": 2},
    {"id": "minecraft:oak_stairs", "count": 16, "price": 2},
    {"id": "minecraft:oak_fence", "count": 16, "price": 2},
    {"id": "minecraft:oak_trapdoor", "count": 16, "price": 2},
    {"id": "minecraft:dark_oak_trapdoor", "count": 16, "price": 2},
    {"id": "minecraft:birch_trapdoor", "count": 16, "price": 2},
    {"id": "minecraft:pale_oak_fence", "count": 16, "price": 2},
    {"id": "minecraft:pale_oak_slab", "count": 16, "price": 2},
    
    # 2. Decorations / Wools / Carpets (16 for 3 Emeralds)
    {"id": "minecraft:white_carpet", "count": 16, "price": 3},
    {"id": "minecraft:light_gray_carpet", "count": 16, "price": 3},
    {"id": "minecraft:white_concrete", "count": 16, "price": 3},
    {"id": "minecraft:light_gray_concrete", "count": 16, "price": 3},
    {"id": "minecraft:black_concrete", "count": 16, "price": 3},
    {"id": "minecraft:dark_oak_door", "count": 16, "price": 3},
    {"id": "minecraft:oak_door", "count": 16, "price": 3},
    {"id": "minecraft:black_stained_glass_pane", "count": 16, "price": 3},
    {"id": "minecraft:glass_pane", "count": 16, "price": 3},
    {"id": "minecraft:white_banner", "count": 16, "price": 3},
    {"id": "minecraft:polished_tuff_slab", "count": 16, "price": 3},
    
    # 3. Leaves / Natural (16 for 3 Emeralds)
    {"id": "minecraft:azalea_leaves", "count": 16, "price": 3},
    {"id": "minecraft:flowering_azalea_leaves", "count": 16, "price": 3},
    {"id": "minecraft:oak_leaves", "count": 16, "price": 3},
    
    # 4. Functional / Utilities (8 for 4 Emeralds, bookshelf is 4 for 6)
    {"id": "minecraft:barrel", "count": 8, "price": 4},
    {"id": "minecraft:bookshelf", "count": 4, "price": 6},
    {"id": "minecraft:chest", "count": 8, "price": 4},
    {"id": "minecraft:composter", "count": 8, "price": 4},
    {"id": "minecraft:furnace", "count": 8, "price": 4},
    
    # 5. Small Items / Utility (8 for 3 Emeralds)
    {"id": "minecraft:flower_pot", "count": 8, "price": 3},
    {"id": "minecraft:stone_button", "count": 8, "price": 3},
    {"id": "minecraft:stone_pressure_plate", "count": 8, "price": 3},
    {"id": "minecraft:tripwire_hook", "count": 8, "price": 3},
    
    # 6. Plants & Vegetation (8 for 3 Emeralds)
    {"id": "minecraft:azure_bluet", "count": 8, "price": 3},
    {"id": "minecraft:dandelion", "count": 8, "price": 3},
    {"id": "minecraft:sea_pickle", "count": 8, "price": 3},
    {"id": "minecraft:short_grass", "count": 8, "price": 3},
    {"id": "minecraft:tall_grass", "count": 8, "price": 3},
    {"id": "minecraft:cherry_sapling", "count": 8, "price": 3},
    {"id": "minecraft:cornflower", "count": 8, "price": 3},
    {"id": "minecraft:lily_of_the_valley", "count": 8, "price": 3},
    
    # 7. Rare / Quartz / Special (4 for 6 Emeralds)
    {"id": "minecraft:smooth_quartz_slab", "count": 4, "price": 6},
    {"id": "minecraft:smooth_quartz_stairs", "count": 4, "price": 6},
    {"id": "minecraft:decorated_pot", "count": 4, "price": 6},
    {"id": "minecraft:light_gray_bed", "count": 4, "price": 6},
    
    # 8. Rare / Lights (4 for 12 Emeralds)
    {"id": "minecraft:lantern", "count": 4, "price": 12},
    {"id": "minecraft:sea_lantern", "count": 4, "price": 12},
]

def main():
    # Revert to original git state first
    print("Reverting save.yml to clean git HEAD...")
    subprocess.run(["git", "checkout", "Shopkeepers/data/save.yml"], cwd=PROJECT_ROOT)
    
    # Re-apply both sets of fixes in order
    print("Re-applying apply_shopkeeper_fixes.py...")
    subprocess.run(["python3", "scripts/apply_shopkeeper_fixes.py"], cwd=PROJECT_ROOT)
    print("Re-applying apply_option2_fixes.py...")
    subprocess.run(["python3", "scripts/apply_option2_fixes.py"], cwd=PROJECT_ROOT)
    
    print(f"Reading save.yml...")
    with open(save_path, 'r') as f:
        lines = f.readlines()
        
    # Find insert position (snapshots: [] under Shopkeeper 1)
    insert_idx = -1
    for idx, line in enumerate(lines):
        if 'snapshots:' in line:
            insert_idx = idx
            break
            
    if insert_idx == -1:
        print("Error: Could not locate 'snapshots:' section for Shopkeeper 1.")
        sys.exit(1)
        
    print(f"Locating snapshots: [] at line {insert_idx + 1}")
    
    # Generate new recipes block
    new_yaml_lines = []
    next_id = 94
    for trade in new_trades:
        new_yaml_lines.extend([
            f"    '{next_id}':\n",
            "      resultItem:\n",
            "        DataVersion: 4903\n",
            f"        id: {trade['id']}\n",
            f"        count: {trade['count']}\n",
            "      item1:\n",
            "        DataVersion: 4903\n",
            "        id: minecraft:emerald\n",
            f"        count: {trade['price']}\n"
        ])
        next_id += 1
        
    # Insert new lines
    lines = lines[:insert_idx] + new_yaml_lines + lines[insert_idx:]
    
    with open(save_path, 'w') as f:
        f.writelines(lines)
        
    print(f"Surgically added {len(new_trades)} trades to Shopkeeper 1 successfully.")

if __name__ == '__main__':
    main()
