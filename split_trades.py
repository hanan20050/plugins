import re

def split_shopkeeper_1():
    with open('Shopkeepers/data/save.yml', 'r') as f:
        content = f.read()

    # We want to extract shopkeeper 1 block and modify it
    # We will split shopkeeper 1 recipes into buy recipes (staying in SK 1) and sell recipes (moving to SK 4 'keeper')
    
    # Read YAML structures carefully using a python script with ruamel or pyyaml if available, or regex line parsing.
    # Let's inspect with standard line parsing to maintain exact formatting.
    
    with open('Shopkeepers/data/save.yml', 'r') as f:
        lines = f.readlines()
        
    sk1_header = []
    sk1_recipes = {} # recipe_num: list of lines
    other_sections = []
    
    current_sk = None
    current_rec = None
    
    sk1_lines = []
    in_sk1 = False
    in_sk1_recipes = False
    
    # Let's parse recipe blocks for SK 1
    sk1_recipes_blocks = []
    current_block = []
    current_rec_id = None
    
    sk1_recipes_dict = {} # rec_id -> {lines: [], is_sell: bool}
    
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("'1':"):
            in_sk1 = True
            sk1_header.append(line)
            i += 1
            while i < len(lines) and not lines[i].startswith("  recipes:"):
                sk1_header.append(lines[i])
                i += 1
            if i < len(lines) and lines[i].startswith("  recipes:"):
                sk1_header.append(lines[i])
                i += 1
            
            # Now inside recipes
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
            in_sk1 = False
        else:
            other_sections.append(line)
            i += 1
            
    # Now classify recipes in sk1_recipes_dict
    buy_rec_blocks = []
    sell_rec_blocks = []
    
    for rec_id, rlines in sk1_recipes_dict.items():
        # Check if resultItem id is emerald
        is_sell = False
        full_text = "".join(rlines)
        # Look for resultItem id
        match = re.search(r"resultItem:\s*\n\s*DataVersion: \d+\s*\n\s*id: ([^\n]+)", full_text)
        if match:
            res_id = match.group(1).strip()
            if res_id == 'minecraft:emerald':
                is_sell = True
        
        if is_sell:
            sell_rec_blocks.append(rlines)
        else:
            buy_rec_blocks.append(rlines)
            
    print(f"Buy recipes count: {len(buy_rec_blocks)}")
    print(f"Sell recipes count: {len(sell_rec_blocks)}")

split_shopkeeper_1()
