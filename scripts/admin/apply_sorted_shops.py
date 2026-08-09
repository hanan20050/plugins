#!/usr/bin/env python3
import re
import os
import sys

SAVE_PATH = 'Shopkeepers/data/save.yml'

def sort_shops():
    if not os.path.exists(SAVE_PATH):
        print("Error: save.yml not found.")
        return False

    with open(SAVE_PATH, 'r') as f:
        content = f.read()

    blocks = re.split(r'\n(?=\'\d+\':)', content)
    new_blocks = []

    for b in blocks:
        m_id = re.search(r'^\s*\'(\d+)\':', b)
        if not m_id:
            new_blocks.append(b)
            continue
        
        sk_id = m_id.group(1)
        if sk_id not in ['1', '4']:
            new_blocks.append(b)
            continue

        m_name = re.search(r'name:\s*([^\n]+)', b)
        sk_name = m_name.group(1) if m_name else 'Unknown'

        # Separate header, recipes, and tail
        rec_start_match = re.search(r'(\n\s+recipes:\s*\n)', b)
        if not rec_start_match:
            new_blocks.append(b)
            continue

        header_part = b[:rec_start_match.end()]
        remainder = b[rec_start_match.end():]

        snap_match = re.search(r'(\n\s+snapshots:.*|\Z)', remainder, re.DOTALL)
        if snap_match and snap_match.group(1):
            tail_part = snap_match.group(1)
            recipes_part = remainder[:snap_match.start()]
        else:
            tail_part = ''
            recipes_part = remainder

        recipe_chunks = re.findall(r'(\s{4}\'\d+\':\s*\n(?:(?!\s{4}\'\d+\':).)*)', recipes_part, re.DOTALL)

        parsed_recs = []
        for r_chunk in recipe_chunks:
            i1_id = re.search(r'item1:\s*\n\s*DataVersion:\s*\d+\s*\n\s*id:\s*([^\n]+)', r_chunk)
            i1_c = re.search(r'item1:\s*\n(?:\s*[^\n]+\n)*?\s*count:\s*(\d+)', r_chunk)
            
            res_id = re.search(r'resultItem:\s*\n\s*DataVersion:\s*\d+\s*\n\s*id:\s*([^\n]+)', r_chunk)
            res_c = re.search(r'resultItem:\s*\n(?:\s*[^\n]+\n)*?\s*count:\s*(\d+)', r_chunk)

            id1 = i1_id.group(1).strip() if i1_id else ''
            c1 = int(i1_c.group(1).strip()) if i1_c else 1
            id_res = res_id.group(1).strip() if res_id else ''
            c_res = int(res_c.group(1).strip()) if res_c else 1

            parsed_recs.append({
                'id1': id1, 'c1': c1,
                'id_res': id_res, 'c_res': c_res,
                'raw': r_chunk
            })

        if sk_id == '1':
            # Remove dry leaves (leaf_litter)
            filtered = [r for r in parsed_recs if r['id1'] != 'minecraft:leaf_litter' and r['id_res'] != 'minecraft:leaf_litter']
            # Sort by price (emerald cost ascending)
            sorted_recs = sorted(filtered, key=lambda r: (r['c1'] if r['id1'] == 'minecraft:emerald' else 0, r['id_res']))
        elif sk_id == '4':
            # Sort SK4 by emerald payout ascending
            sorted_recs = sorted(parsed_recs, key=lambda r: (r['c_res'] if r['id_res'] == 'minecraft:emerald' else 0, r['id1']))
        else:
            sorted_recs = parsed_recs

        new_recipes_str = ""
        for idx, r_data in enumerate(sorted_recs, start=1):
            r_chunk = r_data['raw']
            reindexed_chunk = re.sub(r'^\s{4}\'\d+\':', f"    '{idx}':", r_chunk.lstrip('\n'))
            new_recipes_str += "    " + reindexed_chunk.lstrip()

        cleaned_block = header_part + new_recipes_str + tail_part
        new_blocks.append(cleaned_block)

    new_content = "\n".join(new_blocks)
    with open(SAVE_PATH, 'w') as f:
        f.write(new_content)

    print("Successfully sorted shops and removed dry leaves!")
    return True

if __name__ == '__main__':
    sort_shops()
