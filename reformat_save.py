import re

def reformat_save():
    with open('Shopkeepers/data/save.yml', 'r') as f:
        lines = f.readlines()
        
    sk1_header = []
    sk1_recipes_dict = {}
    
    i = 0
    sk1_end_idx = 0
    
    while i < len(lines):
        line = lines[i]
        if line.startswith("'1':"):
            sk1_header.append(line)
            i += 1
            while i < len(lines) and not lines[i].startswith("  recipes:"):
                sk1_header.append(lines[i])
                i += 1
            if i < len(lines) and lines[i].startswith("  recipes:"):
                sk1_header.append(lines[i])
                i += 1
            
            curr_id = None
            curr_lines = []
            while i < len(lines) and not lines[i].startswith("  snapshots:") and not (len(lines[i]) - len(lines[i].lstrip()) == 0 and lines[i].strip() and not lines[i].startswith('#')):
                l = lines[i]
                if l.startswith("    '"):
                    if curr_id is not None:
                        sk1_recipes_dict[curr_id] = curr_lines
                    curr_id = l.strip().replace("'", "").replace(":", "")
                    curr_lines = [l]
                else:
                    curr_lines.append(l)
                i += 1
            if curr_id is not None:
                sk1_recipes_dict[curr_id] = curr_lines
            sk1_end_idx = i
            break
        i += 1

    remaining_lines = lines[sk1_end_idx:]
    
    buy_rec_blocks = []
    sell_rec_blocks = []
    
    for rec_id in sorted(sk1_recipes_dict.keys(), key=lambda x: int(x)):
        rlines = sk1_recipes_dict[rec_id]
        full_text = "".join(rlines)
        match = re.search(r"resultItem:\s*\n\s*DataVersion: \d+\s*\n\s*id: ([^\n]+)", full_text)
        is_sell = False
        if match:
            res_id = match.group(1).strip()
            if res_id == 'minecraft:emerald':
                is_sell = True
        
        if is_sell:
            sell_rec_blocks.append(rlines)
        else:
            buy_rec_blocks.append(rlines)

    # Reconstruct SK1 with buy_rec_blocks
    new_sk1_lines = list(sk1_header)
    for idx, block in enumerate(buy_rec_blocks, start=1):
        # Update recipe index line
        first_line = f"    '{idx}':\n"
        new_sk1_lines.append(first_line)
        new_sk1_lines.extend(block[1:])
        
    new_sk1_lines.append("  snapshots: []\n")

    # Construct SK4 ('keeper') with sell_rec_blocks
    # Position SK4 to the left of SK1 (SK1 is at x: 1297, y: 80, z: -218, yaw: 88.36158).
    # To place it on the left (or next to it, e.g., z: -220 or x: 1297, z: -220):
    sk4_header = [
        "'4':\n",
        "  uniqueId: e8f2b3c4-75d9-4b12-a3e4-829104756182\n",
        "  world: world\n",
        "  x: 1297\n",
        "  y: 80\n",
        "  z: -220\n",
        "  yaw: 88.36158\n",
        "  type: admin\n",
        "  open: true\n",
        "  name: '&aKeeper'\n",
        "  object:\n",
        "    type: villager\n",
        "    baby: false\n",
        "    profession: minecraft:nitwit\n",
        "    villagerType: minecraft:plains\n",
        "    villagerLevel: 2\n",
        "  recipes:\n"
    ]
    
    new_sk4_lines = list(sk4_header)
    for idx, block in enumerate(sell_rec_blocks, start=1):
        first_line = f"    '{idx}':\n"
        new_sk4_lines.append(first_line)
        new_sk4_lines.extend(block[1:])
        
    new_sk4_lines.append("  snapshots: []\n")

    # Combine everything
    # We take lines before SK1 (data-version: ...), new SK1, remaining lines (SK2, SK3), and append SK4 at the end.
    
    with open('Shopkeepers/data/save.yml', 'w') as f:
        f.writelines(lines[:3]) # header comments / data-version
        f.writelines(new_sk1_lines)
        f.writelines(remaining_lines)
        f.writelines(new_sk4_lines)

    print("save.yml successfully updated!")

reformat_save()
