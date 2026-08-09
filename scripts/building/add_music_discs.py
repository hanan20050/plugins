import os
import sys

# Paths setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
save_path = os.path.join(PROJECT_ROOT, "Shopkeepers/data/save.yml")

music_discs = [
    # Common Music Discs (1 for 8 Emeralds)
    {"id": "minecraft:music_disc_13", "price": 8},
    {"id": "minecraft:music_disc_cat", "price": 8},
    {"id": "minecraft:music_disc_blocks", "price": 8},
    {"id": "minecraft:music_disc_chirp", "price": 8},
    {"id": "minecraft:music_disc_far", "price": 8},
    {"id": "minecraft:music_disc_mall", "price": 8},
    {"id": "minecraft:music_disc_mellohi", "price": 8},
    {"id": "minecraft:music_disc_stal", "price": 8},
    {"id": "minecraft:music_disc_strad", "price": 8},
    {"id": "minecraft:music_disc_ward", "price": 8},
    {"id": "minecraft:music_disc_11", "price": 8},
    {"id": "minecraft:music_disc_wait", "price": 8},
    
    # Rare Music Discs (1 for 16 Emeralds)
    {"id": "minecraft:music_disc_otherside", "price": 16},
    {"id": "minecraft:music_disc_5", "price": 16},
    {"id": "minecraft:music_disc_relic", "price": 16},
    {"id": "minecraft:music_disc_creator_music_box", "price": 16},
    {"id": "minecraft:music_disc_precipice", "price": 16},
    
    # Epic Music Discs (1 for 32 Emeralds)
    {"id": "minecraft:music_disc_pigstep", "price": 32},
    {"id": "minecraft:music_disc_creator", "price": 32},
]

def main():
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
        
    print(f"Locating insert point at line {insert_idx + 1}")
    
    # Let's find what the last recipe ID is to start indexing from there
    # We can scan backwards from insert_idx to find the last trade ID
    last_recipe_id = 140
    for idx in range(insert_idx - 1, 0, -1):
        line = lines[idx].strip()
        if line.endswith("':") and line.startswith("'"):
            try:
                last_recipe_id = int(line.replace("'", "").replace(":", ""))
                break
            except ValueError:
                pass
                
    next_id = last_recipe_id + 1
    print(f"Adding music discs starting from recipe ID: {next_id}")
    
    new_yaml_lines = []
    for disc in music_discs:
        new_yaml_lines.extend([
            f"    '{next_id}':\n",
            "      resultItem:\n",
            "        DataVersion: 4903\n",
            f"        id: {disc['id']}\n",
            "        count: 1\n",
            "      item1:\n",
            "        DataVersion: 4903\n",
            "        id: minecraft:emerald\n",
            f"        count: {disc['price']}\n"
        ])
        next_id += 1
        
    # Insert new lines
    lines = lines[:insert_idx] + new_yaml_lines + lines[insert_idx:]
    
    with open(save_path, 'w') as f:
        f.writelines(lines)
        
    print(f"Surgically added {len(music_discs)} music discs to Shopkeeper 1 successfully.")

if __name__ == '__main__':
    main()
