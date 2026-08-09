import shutil
import os

save_path = "/Users/hanansaleh/Downloads/plugins/Shopkeepers/data/save.yml"
backup_path = save_path + ".bak"

# 1. Create backup
print(f"Creating backup: {backup_path}")
shutil.copy2(save_path, backup_path)

with open(save_path, 'r') as f:
    lines = f.readlines()

# Define targeted replacements based on line numbers (0-indexed = line number - 1)
# Recipe 7 (Bow): Lines 1114-1122
# 1121:         id: minecraft:bow
# 1122:         count: 1
print("Updating Recipe 7 (Bow count from 1 to 3)...")
if "id: minecraft:bow" in lines[1120] and "count: 1" in lines[1121]:
    lines[1121] = lines[1121].replace("count: 1", "count: 3")
else:
    print("Warning: Expected lines for Recipe 7 not found at target lines. Checking dynamically...")
    # fallback search
    for i in range(1100, 1130):
        if "id: minecraft:bow" in lines[i] and "count: 1" in lines[i+1]:
            lines[i+1] = lines[i+1].replace("count: 1", "count: 3")
            break

# Recipe 46 (Saddle): Lines 1465-1473
# 1472:         id: minecraft:saddle
# 1473:         count: 1
print("Updating Recipe 46 (Saddle count from 1 to 2)...")
if "id: minecraft:saddle" in lines[1471] and "count: 1" in lines[1472]:
    lines[1472] = lines[1472].replace("count: 1", "count: 2")
else:
    print("Warning: Expected lines for Recipe 46 not found at target lines. Checking dynamically...")
    for i in range(1450, 1490):
        if "id: minecraft:saddle" in lines[i] and "count: 1" in lines[i+1]:
            lines[i+1] = lines[i+1].replace("count: 1", "count: 2")
            break

# Recipe 52 (Stone): Lines 1519-1527
# 1526:         id: minecraft:stone
# 1527:         count: 21
print("Updating Recipe 52 (Stone count from 21 to 32)...")
if "id: minecraft:stone" in lines[1525] and "count: 21" in lines[1526]:
    lines[1526] = lines[1526].replace("count: 21", "count: 32")
else:
    print("Warning: Expected lines for Recipe 52 not found at target lines. Checking dynamically...")
    for i in range(1500, 1540):
        if "id: minecraft:stone" in lines[i] and "count: 21" in lines[i+1]:
            lines[i+1] = lines[i+1].replace("count: 21", "count: 32")
            break

with open(save_path, 'w') as f:
    f.writelines(lines)

print("Shopkeepers save file successfully updated and saved locally!")
