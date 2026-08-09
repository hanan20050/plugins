import yaml

save_path = "Shopkeepers/data/save.yml"

with open(save_path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

converted_count = 0

def convert_emerald_blocks(obj):
    global converted_count
    if isinstance(obj, dict):
        if "recipes" in obj:
            recipes = obj["recipes"]
            for r_key, recipe in list(recipes.items()):
                item1 = recipe.get("item1", {})
                item2 = recipe.get("item2", {})
                
                # Check item1
                if item1.get("id") == "minecraft:emerald_block":
                    c = item1.get("count", 1)
                    item1["id"] = "minecraft:heavy_core"
                    item1["count"] = min(64, c * 9)
                    converted_count += 1
                
                # Check item2
                if item2.get("id") == "minecraft:emerald_block":
                    c = item2.get("count", 1)
                    # If item1 is heavy_core, combine or convert item2 to heavy_core
                    if item1.get("id") == "minecraft:heavy_core":
                        added_count = c * 9
                        total = item1.get("count", 0) + added_count
                        if total <= 64:
                            item1["count"] = total
                            del recipe["item2"]
                        else:
                            item1["count"] = 64
                            item2["id"] = "minecraft:heavy_core"
                            item2["count"] = min(64, total - 64)
                    else:
                        item2["id"] = "minecraft:heavy_core"
                        item2["count"] = min(64, c * 9)
                    converted_count += 1
                    
        for v in obj.values():
            if isinstance(v, (dict, list)):
                convert_emerald_blocks(v)
    elif isinstance(obj, list):
        for item in obj:
            convert_emerald_blocks(item)

convert_emerald_blocks(data)

with open(save_path, "w", encoding="utf-8") as f:
    yaml.safe_dump(data, f, sort_keys=False)

print(f"Converted {converted_count} emerald_block occurrences to heavy_core (1 block = 9 heavy_core, capped at 64).")
