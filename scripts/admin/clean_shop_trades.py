#!/usr/bin/env python3
import re
import os
import sys

SAVE_PATH = 'Shopkeepers/data/save.yml'

def clean_save_file(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} does not exist.")
        return False

    with open(filepath, 'r') as f:
        content = f.read()

    currency_items = {'minecraft:emerald', 'minecraft:emerald_block', 'minecraft:netherite_ingot', 'minecraft:netherite_block'}

    # Split top-level blocks by shopkeeper keys (e.g. '1':, '2':, '4':, '5':)
    sk_blocks = re.split(r'\n(?=\'\d+\':)', content)
    
    seen_sk_ids = set()
    cleaned_blocks = []

    for block in sk_blocks:
        if not block.strip():
            continue
        
        m_id = re.match(r'^\s*\'(\d+)\':', block)
        if not m_id:
            cleaned_blocks.append(block)
            continue
        
        sk_id = m_id.group(1)
        
        # Deduplicate top-level shopkeepers by ID
        if sk_id in seen_sk_ids:
            m_name = re.search(r'name:\s*([^\n]+)', block)
            sk_name = m_name.group(1) if m_name else 'Unknown'
            print(f"[Deduplication] Removing duplicate top-level Shopkeeper ID {sk_id} ({sk_name})")
            continue
        
        seen_sk_ids.add(sk_id)
        
        m_name = re.search(r'name:\s*([^\n]+)', block)
        sk_name = m_name.group(1) if m_name else 'Unknown'

        # Extract header before recipes
        rec_start_match = re.search(r'(\n\s+recipes:\s*\n)', block)
        if not rec_start_match:
            cleaned_blocks.append(block)
            continue

        header_part = block[:rec_start_match.end()]
        remainder = block[rec_start_match.end():]

        # Extract snapshots or tail
        snap_match = re.search(r'(\n\s+snapshots:.*|\Z)', remainder, re.DOTALL)
        if snap_match and snap_match.group(1):
            tail_part = snap_match.group(1)
            recipes_part = remainder[:snap_match.start()]
        else:
            tail_part = ''
            recipes_part = remainder

        # Parse individual recipe chunks inside recipes_part
        # Recipe block starts with 4 spaces indent, e.g. "    '1':\n"
        recipe_chunks = re.findall(r'(\s{4}\'\d+\':\s*\n(?:(?!\s{4}\'\d+\':).)*)', recipes_part, re.DOTALL)

        seen_signatures = set()
        kept_recipe_chunks = []

        for r_chunk in recipe_chunks:
            i1_id = re.search(r'item1:\s*\n\s*DataVersion:\s*\d+\s*\n\s*id:\s*([^\n]+)', r_chunk)
            i1_c = re.search(r'item1:\s*\n(?:\s*[^\n]+\n)*?\s*count:\s*(\d+)', r_chunk)
            
            res_id = re.search(r'resultItem:\s*\n\s*DataVersion:\s*\d+\s*\n\s*id:\s*([^\n]+)', r_chunk)
            res_c = re.search(r'resultItem:\s*\n(?:\s*[^\n]+\n)*?\s*count:\s*(\d+)', r_chunk)

            comp = re.search(r'components:\s*([^\n]+(?:\n\s+[^\n]+)*)', r_chunk)
            comp_str = comp.group(1).strip() if comp else ''

            id1 = i1_id.group(1).strip() if i1_id else None
            c1 = i1_c.group(1).strip() if i1_c else '1'
            id_res = res_id.group(1).strip() if res_id else None
            c_res = res_c.group(1).strip() if res_c else '1'

            signature = (id1, c1, id_res, c_res, comp_str)
            is_exchange = (id1 in currency_items) and (id_res in currency_items)

            # Remove exchange trades from non-Money Exchange shopkeepers
            if sk_id != '5' and is_exchange:
                print(f"[Shopkeeper {sk_id} ({sk_name})] Removing exchange trade: {c1}x {id1} -> {c_res}x {id_res}")
                continue

            # Remove duplicate trades within the same shopkeeper
            if signature in seen_signatures:
                print(f"[Shopkeeper {sk_id} ({sk_name})] Removing duplicate trade: {c1}x {id1} -> {c_res}x {id_res}")
                continue

            seen_signatures.add(signature)
            kept_recipe_chunks.append(r_chunk)

        # Re-index remaining recipes starting from 1
        new_recipes_str = ""
        for idx, r_chunk in enumerate(kept_recipe_chunks, start=1):
            reindexed_chunk = re.sub(r'^\s{4}\'\d+\':', f"    '{idx}':", r_chunk.lstrip('\n'))
            new_recipes_str += "    " + reindexed_chunk.lstrip()

        cleaned_block = header_part + new_recipes_str + tail_part
        cleaned_blocks.append(cleaned_block)

    new_content = "\n".join(cleaned_blocks)
    with open(filepath, 'w') as f:
        f.write(new_content)

    print(f"Successfully cleaned {filepath}!")
    return True

if __name__ == '__main__':
    clean_save_file(SAVE_PATH)
