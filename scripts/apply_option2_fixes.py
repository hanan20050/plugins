import shutil
import os

save_path = "/Users/hanansaleh/Downloads/plugins/Shopkeepers/data/save.yml"
backup_path = save_path + ".bak"

# 1. Create backup
print(f"Updating backup: {backup_path}")
shutil.copy2(save_path, backup_path)

with open(save_path, 'r') as f:
    lines = f.readlines()

# Shopkeeper 1, Recipe 45 (String): Change count from 12 to 8
# 420:         id: minecraft:string
# 421:         count: 12
print("Updating Shopkeeper 1, Recipe 45 (String count 12 -> 8)...")
if "id: minecraft:string" in lines[419] and "count: 12" in lines[420]:
    lines[420] = lines[420].replace("count: 12", "count: 8")
else:
    print("Warning: Expected lines for Recipe 45 not found at target lines. Checking dynamically...")
    for i in range(400, 440):
        if "id: minecraft:string" in lines[i] and "count: 12" in lines[i+1]:
            lines[i+1] = lines[i+1].replace("count: 12", "count: 8")
            break

# Shopkeeper 1, Recipe 56 (Stick): Change count from 32 to 16
# 519:         id: minecraft:stick
# 520:         count: 32
print("Updating Shopkeeper 1, Recipe 56 (Stick count 32 -> 16)...")
if "id: minecraft:stick" in lines[518] and "count: 32" in lines[519]:
    lines[519] = lines[519].replace("count: 32", "count: 16")
else:
    print("Warning: Expected lines for Recipe 56 not found at target lines. Checking dynamically...")
    for i in range(500, 540):
        if "id: minecraft:stick" in lines[i] and "count: 32" in lines[i+1]:
            lines[i+1] = lines[i+1].replace("count: 32", "count: 16")
            break

# Shopkeeper 4, Recipe 7 (Bow): Change count from 3 to 2
# 1121:         id: minecraft:bow
# 1122:         count: 3
print("Updating Shopkeeper 4, Recipe 7 (Bow count 3 -> 2)...")
if "id: minecraft:bow" in lines[1120] and "count: 3" in lines[1121]:
    lines[1121] = lines[1121].replace("count: 3", "count: 2")
else:
    print("Warning: Expected lines for Recipe 7 not found at target lines. Checking dynamically...")
    for i in range(1100, 1140):
        if "id: minecraft:bow" in lines[i] and "count: 3" in lines[i+1]:
            lines[i+1] = lines[i+1].replace("count: 3", "count: 2")
            break

with open(save_path, 'w') as f:
    f.writelines(lines)

print("Shopkeepers save file successfully updated with Option 2 fixes!")
