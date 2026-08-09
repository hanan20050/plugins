import yaml

save_path = "Shopkeepers/data/save.yml"

with open(save_path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

replaced_count = 0

def replace_emerald(obj):
    global replaced_count
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "id" and v == "minecraft:emerald":
                obj[k] = "minecraft:heavy_core"
                replaced_count += 1
            else:
                replace_emerald(v)
    elif isinstance(obj, list):
        for item in obj:
            replace_emerald(item)

replace_emerald(data)

with open(save_path, "w", encoding="utf-8") as f:
    yaml.safe_dump(data, f, sort_keys=False)

print(f"Replaced {replaced_count} instances of minecraft:emerald with minecraft:heavy_core in save.yml.")
