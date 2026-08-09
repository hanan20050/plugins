#!/usr/bin/env python3
import re
import os

SAVE_PATH = 'Shopkeepers/data/save.yml'

def surgical_sort():
    with open(SAVE_PATH, 'r') as f:
        content = f.read()

    currency_items = {'minecraft:emerald', 'minecraft:emerald_block', 'minecraft:netherite_ingot', 'minecraft:netherite_block'}

    # Split shopkeeper blocks by top-level shopkeeper keys: '1':, '2':, '4':, '5':
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
            tail_part = '  snapshots: []\n'
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
            # Remove dry leaves (leaf_litter) and exchange trades
            filtered = [r for r in parsed_recs if r['id1'] != 'minecraft:leaf_litter' and r['id_res'] != 'minecraft:leaf_litter' and not (r['id1'] in currency_items and r['id_res'] in currency_items)]
            # Sort SK1: emerald cost ascending (if item1 is emerald), then by result item id
            sorted_recs = sorted(filtered, key=lambda r: (
                0 if r['id1'] != 'minecraft:emerald' else 1,
                r['c1'] if r['id1'] == 'minecraft:emerald' else 0,
                r['id_res']
            ))
        elif sk_id == '4':
            # Remove exchange trades and duplicates
            seen = set()
            filtered = []
            for r in parsed_recs:
                if r['id1'] in currency_items and r['id_res'] in currency_items:
                    continue
                sig = (r['id1'], r['c1'], r['id_res'], r['c_res'])
                if sig in seen:
                    continue
                seen.add(sig)
                filtered.append(r)
            # Sort SK4: emerald payout ascending (if resultItem is emerald), then by item1 id
            sorted_recs = sorted(filtered, key=lambda r: (
                0 if r['id_res'] != 'minecraft:emerald' else 1,
                r['c_res'] if r['id_res'] == 'minecraft:emerald' else 0,
                r['id1']
            ))

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

    print("Surgical sort and cleanup complete!")
    return True

if __name__ == '__main__':
    surgical_sort()
