#!/usr/bin/env python3
import os
import sys
import yaml
import argparse
import subprocess

# Paths
PLUGINS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_PATH = os.path.join(PLUGINS_DIR, "Shopkeepers/data/save.yml")
SYNC_PATH = os.path.join(PLUGINS_DIR, "sync.py")

# Biome item mappings
BIOME_ITEMS = {
    "ancient_city": [
        "minecraft:echo_shard",
        "minecraft:disc_fragment_5",
        "minecraft:ward_armor_trim_smithing_template",
        "minecraft:silence_armor_trim_smithing_template",
        "minecraft:sculk",
        "minecraft:sculk_sensor",
        "minecraft:sculk_catalyst",
        "minecraft:sculk_shrieker",
        "minecraft:sculk_vein"
    ],
    "ocean_monument": [
        "minecraft:sponge",
        "minecraft:nautilus_shell",
        "minecraft:heart_of_the_sea",
        "minecraft:prismarine_shard",
        "minecraft:prismarine_crystals",
        "minecraft:tide_armor_trim_smithing_template"
    ],
    "nether": [
        "minecraft:wither_skeleton_skull",
        "minecraft:blaze_rod",
        "minecraft:ghast_tear",
        "minecraft:nether_wart",
        "minecraft:ancient_debris",
        "minecraft:netherite_scrap"
    ],
    "end": [
        "minecraft:elytra",
        "minecraft:shulker_shell",
        "minecraft:dragon_head",
        "minecraft:end_crystal"
    ]
}

def main():
    parser = argparse.ArgumentParser(description="Ensure items are exploration-only by removing them from buying shops.")
    parser.add_argument("--biome", choices=list(BIOME_ITEMS.keys()), help="Set all items of this biome to exploration-only.")
    parser.add_argument("--items", nargs="+", help="Specific item IDs to make exploration-only.")
    parser.add_argument("--no-push", action="store_true", help="Do not push changes to the Exaroton server automatically.")
    
    args = parser.parse_args()
    
    if not args.biome and not args.items:
        parser.print_help()
        sys.exit(1)
        
    # Gather target items
    target_items = []
    if args.biome:
        target_items.extend(BIOME_ITEMS[args.biome])
    if args.items:
        target_items.extend(args.items)
        
    target_items = list(set(target_items)) # unique
    print(f"Target items to make exploration-only: {target_items}")
    
    # Load save.yml
    if not os.path.exists(SAVE_PATH):
        print(f"Error: save.yml not found at {SAVE_PATH}")
        sys.exit(1)
        
    with open(SAVE_PATH, "r") as f:
        data = yaml.safe_load(f)
        
    removed_count = 0
    # Search all buy shops (we check all shops EXCEPT Shopkeeper 4 which is Sell, and 5 which is Money Exchange)
    # Actually, we check Shopkeepers 1 (General Store), 2 (Upgrades), and 6 (Books)
    buy_shop_ids = ["1", "2", "6"]
    
    for sk_id in buy_shop_ids:
        sk = data.get(sk_id)
        if not sk:
            continue
            
        recipes = sk.get("recipes", {})
        for r_id in list(recipes.keys()):
            res = recipes[r_id].get("resultItem", {})
            if res.get("id") in target_items:
                del recipes[r_id]
                removed_count += 1
                print(f"Removed buy trade {r_id} ({res.get('id')}) from Shopkeeper {sk_id} ({sk.get('name')})")
                
    if removed_count == 0:
        print("No buy trades found for any of the target items. They are already exploration-only in the buying shops!")
        return
        
    # Save save.yml
    with open(SAVE_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
    print(f"Successfully removed {removed_count} trades and updated save.yml.")
    
    # Push and reload
    if not args.no_push:
        print("Pushing updated save.yml to server...")
        try:
            res = subprocess.run([sys.executable, SYNC_PATH, "push", "Shopkeepers/data/save.yml"], check=True)
            print("Successfully synced and reloaded Shopkeepers on the server.")
        except subprocess.CalledProcessError as e:
            print("Error syncing changes to server:", e)
            sys.exit(1)

if __name__ == "__main__":
    main()
